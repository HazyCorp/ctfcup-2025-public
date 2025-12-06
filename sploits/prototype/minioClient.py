#!/usr/bin/env python3
import sys
import ssl
import requests
import xml.etree.ElementTree as ET
import urllib3
from urllib.parse import urlparse
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



class MinioS3Client:
    def __init__(self, endpoint_with_s3, access_key, secret_key, region='us-east-1',
                 minio_internal_host='prototype-minio.prototype.svc.cluster.local:9000'):
        
        self.endpoint = endpoint_with_s3.rstrip('/')
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        
        parsed = urlparse(self.endpoint)
        self.request_host = parsed.netloc
        self.scheme = parsed.scheme
        self.signature_host = minio_internal_host
        
        # Disable SSL warnings for self-signed certificates
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        requests.packages.urllib3.disable_warnings()
        
        self._setup_admin_client(access_key, secret_key, minio_internal_host)
    
    def _setup_admin_client(self, access_key, secret_key, minio_internal_host):
        try:
            import minio
            from minio.credentials.providers import StaticProvider
            
            class S3ProxyHTTPAdapter(urllib3.poolmanager.PoolManager):
                def __init__(self, proxy_endpoint, *args, **kwargs):
                    # Create SSL context that ignores certificate verification
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    # Support TLS 1.3
                    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3
                    ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
                    
                    kwargs['ssl_context'] = ssl_context
                    kwargs['cert_reqs'] = ssl.CERT_NONE
                    kwargs['assert_hostname'] = False
                    
                    super().__init__(*args, **kwargs)
                    self.proxy_endpoint = proxy_endpoint
                
                def urlopen(self, method, url, *args, **kwargs):
                    if url.startswith('http://') or url.startswith('https://'):
                        from urllib.parse import urlparse, urlunparse
                        parsed = urlparse(url)
                        proxy_parsed = urlparse(self.proxy_endpoint)
                        new_path = '/s3' + parsed.path
                        new_url = urlunparse((
                            proxy_parsed.scheme,
                            proxy_parsed.netloc,
                            new_path,
                            parsed.params,
                            parsed.query,
                            parsed.fragment
                        ))
                        url = new_url
                    
                    return super().urlopen(method, url, *args, **kwargs)
            
            http_client = S3ProxyHTTPAdapter(
                self.endpoint,
                timeout=urllib3.Timeout(connect=5.0, read=30.0),
                retries=False,
            )
            
            self.admin_client = minio.MinioAdmin(
                endpoint=minio_internal_host,
                credentials=StaticProvider(access_key, secret_key),
                secure=False,
                http_client=http_client
            )
        except ImportError:
            print("WARNING: minio library not available, Admin API disabled", file=sys.stderr)
            self.admin_client = None
        except Exception as e:
            print(f"WARNING: Failed to setup Admin client: {e}", file=sys.stderr)
            self.admin_client = None
    
    def _request(self, method, path_after_rewrite, data=b'', query_string=''):
        """
        Выполнить HTTP запрос используя botocore для подписи
        """
        # URL для запроса (с /s3/)
        url = f"{self.endpoint}{path_after_rewrite}"
        if query_string:
            url += f"?{query_string}"
        
        # URL для подписи (как MinIO увидит)
        signature_url = f"{self.scheme}://{self.signature_host}{path_after_rewrite}"
        if query_string:
            signature_url += f"?{query_string}"
        
        # Создаем AWS credentials
        credentials = Credentials(self.access_key, self.secret_key)
        
        # Создаем AWS request для подписи
        aws_request = AWSRequest(
            method=method,
            url=signature_url,
            data=data,
            headers={
                'Host': self.signature_host,
                'Content-Type': 'application/octet-stream'
            }
        )
        
        # Подписываем запрос используя botocore
        SigV4Auth(credentials, 's3', self.region).add_auth(aws_request)
        
        # Отправляем запрос на реальный URL (с /s3/)
        response = requests.request(
            method,
            url,
            headers={
                'Host': self.request_host,
                'Authorization': aws_request.headers['Authorization'],
                'x-amz-date': aws_request.headers['x-amz-date'],
                'x-amz-content-sha256': aws_request.headers['x-amz-content-sha256'],
                'Content-Type': 'application/octet-stream'
            },
            data=data,
            verify=False
        )
        
        return response
    
    def list_buckets(self):
        try:
            response = self._request('GET', '/')
            
            if response.status_code != 200:
                print(f"Error: HTTP {response.status_code}", file=sys.stderr)
                print(response.text, file=sys.stderr)
                return []
            
            root = ET.fromstring(response.content)
            buckets = []
            
            for bucket in root.findall('.//{http://s3.amazonaws.com/doc/2006-03-01/}Bucket'):
                name = bucket.find('{http://s3.amazonaws.com/doc/2006-03-01/}Name').text
                created = bucket.find('{http://s3.amazonaws.com/doc/2006-03-01/}CreationDate').text
                buckets.append({'name': name, 'created': created})
            
            return buckets
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return []
    
    def list_objects(self, bucket, prefix='', max_keys=1000):
        try:
            path = f"/{bucket}/"
            query_string = f"list-type=2&max-keys={max_keys}"
            if prefix:
                query_string += f"&prefix={prefix}"
            
            response = self._request('GET', path, query_string=query_string)
            
            if response.status_code != 200:
                print(f"Error: HTTP {response.status_code}", file=sys.stderr)
                print(response.text, file=sys.stderr)
                return []
            
            root = ET.fromstring(response.content)
            objects = []
            
            for obj in root.findall('.//{http://s3.amazonaws.com/doc/2006-03-01/}Contents'):
                key = obj.find('{http://s3.amazonaws.com/doc/2006-03-01/}Key').text
                size = int(obj.find('{http://s3.amazonaws.com/doc/2006-03-01/}Size').text)
                last_modified = obj.find('{http://s3.amazonaws.com/doc/2006-03-01/}LastModified').text
                etag = obj.find('{http://s3.amazonaws.com/doc/2006-03-01/}ETag').text.strip('"')
                
                objects.append({
                    'key': key,
                    'size': size,
                    'last_modified': last_modified,
                    'etag': etag
                })
            
            return objects
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return []
    
    def get_object(self, bucket, key, output_file=None):
        try:
            path = f"/{bucket}/{key}"
            response = self._request('GET', path)
            
            if response.status_code != 200:
                print(f"Error: HTTP {response.status_code}", file=sys.stderr)
                print(response.text, file=sys.stderr)
                return None
            
            if output_file:
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                return response.content
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return None
    
    def create_service_account(self, sa_access_key, sa_secret_key, policy=None):
        if not self.admin_client:
            print("Error: MinIO Admin client not available", file=sys.stderr)
            return None
        
        try:
            sa_access_key = sa_access_key[:20]
            sa_secret_key = sa_secret_key[:40]
            
            self.admin_client.add_service_account(
                access_key=sa_access_key,
                secret_key=sa_secret_key,
                policy=policy
            )

            return {
                'access_key': sa_access_key,
                'secret_key': sa_secret_key,
                'status': 'created'
            }
        except Exception as e:
            print(f"Error creating service account: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return None

