# Warehouse
## Базовый сценарий
Пользователь проходит регистрацию на `auth-server`, затем аутентифицируется на warehouse, создает свой склад-реалм, в который можно добавить других пользователей, зарегистрированных на `auth-server`. 

Затем, внутри склада-реалма, можно добавить различные позиции и назначить ответственного владельца из числа пользователей, присоединенных к складу.

Также доступна функциональность по обеспечению безопасности доступа к складу  и защиты от вредоносного трафика. Реализуется это через создание и настройку обратного прокси на сервисе `gateway-server`, к которому можно подлючить TI-фиды с разведданными о вредоностной активности, по которым в свою очередь будет приниматься решение о блокировке запроса или только мониторинг.

### Все фичи
**warehouse**:
- создание склада;
- добавление позиций в склад;
- добавление пользователей к складу и назначение ролей;
- назначение ответственных за позиции в складе

**auth-server**:
- регистраций пользователей;
- аутентификация пользователей;
- oauth-эндпоинт.

**ti-server**:
- добавление приватных/публичных фидов;
- добавление индикаторов компрометации в фиды;
- авторизация к приватным фидам.

**gateway-server**:
- создание виртуального сервиса;
- настройка виртуального сервиса: 
    - назначение url;
    - path-slug;
    - настройка рейт-лимитера;
    - настройка TI-фидов;
    - выбор TI режима: блокировка, мониторинг, отключен;
    - логгирование сработок по IOC из TI-фидов.

## Архитектура
Сервис состоит из четырех микросервисов:
- [auth-server](../../services/warehouse/src/auth-server/) — сервис аутентификации и identity provider;
- [gateway-server](../../services/warehouse/src/gateway-server/) — http-гейтвей с функциями анализа трафика по TI-фидам;
- [ti-server](../../services/warehouse/src/ti-server/) — TI сервер для размещения фидов;
- [warehouse](../../services/warehouse/src/warehouse/) — веб-сервис для учета барного склада.

При этом реализуется межсервисное взаимодействие:
- `auth-server <-> warehouse` — oauth аутентификация;
- `warehouse -> auth-server` — получение списка пользователей для добавления к складу;
- `auth-server <-> gateway-server` — oauth аутентификация;
- `warehouse -> gateway` — API запрос на создание gateway-server.

Все сервисы хранят свои данные в едином инстансе PostgreSQL в разных базах данных, название которых соответствует сервису. 

Кроме того, все сервисы выставлены с хоста через [Ingress](../../services/warehouse/deploy/chart/templates/ingress.yaml) [nginx](../../services/warehouse/deploy/chart/charts/), который обеспечивает TLS, а также маршрутизацию запросов по пути HTTP-запроса в соответствующий сервис.

## Уязвимости
1. Генерация API Key в ti-server с использованием UUIDv1 приводит к возможности несанкционированного доступа к индикаторам компрометации в приватных фидах;
2. SSRF в gateway-server приводит к возможности реализации запросов на внутренний обработчик, что ведет к получению расширенной информации о пользователях.

## Эксплуатация

### Генерация API Key в ti-server
Если обратиться к [коду](../../services/warehouse/src/ti-server/internal/storage/postgres.go#L62), где происходит генерация API ключа для приватного фида, можно увидеть, что генерация происходит аналогично идентификатору фида, а именно за счет использования `UUIDv1` (документация по библиотеке может на это указать, в IDE подсвечивается ;-) ). Первая часть `UUIDv1` зависит от времени генерации, а вторая является статичной в зависимости от хоста.

Главный вывод, который здесь можно сделать — это то, что зная время генерации и вторую часть UUID'а, можно подобрать API ключ к приватному фиду. Здесь нам на помощь приходит идентификатор приватного фида, который генерируется примерно в то же время, что и ключ, а также имеет аналогичную вторую часть. Таким образом, получив идентификатор фида (которые можно получить из чексистемы или из запроса к api `ti-server`), у нас появляется возможность сгененировать API ключ к этому же приватному фиду.

Пример UUIDv1:
```
876292e2-d1fa-11f0-8de9-0242ac120002
\______/ \_________________________/
   ^                  ^
Зависимая         Зависимая от сервера часть
от времени часть          (статична)
```
Сама атака реализуется следующим образом:
1. Получаем идентификатор приватного фида;
2. Брутфорсим зависимую от времени часть идентификатора с проверкой в качетсве API ключа на сервере, откуда был получен идентификатор. В среднем не более чем за 5-7 итераций удается попасть в нужный ключ. *(примечание: API ключ — это не просто `UUIDv1`, это `md5(UUIDv1)`; важно не забыть хэшировать перед запросом к API)*

### SSRF в gateway-server
`Auth-server`, при запросах типа [/users/search?query=](../../services/warehouse/src/auth-server/cmd/server/main.go#L139-L145), реализует функциональность поиска пользователя по подстроке. Это необходимо, чтобы динамически получать информацию о пользователях при их подключении к складу в `warehouse` (удобный интерфейс для поиска, то самое межсервисное взаимодействие, о котором упоминалось выше). [Хэндлер](../../services/warehouse/src/auth-server/internal/handlers/handlers.go#L233), отвечающий за этот путь, возвращает чуть больше информации чем требуется, а именно — [email пользователя](../../services/warehouse/src/auth-server/internal/storage/postgres.go#L239). Об этом косвенно свидетельствует функциональность, для которой существуюет данный хэндлер — в списке пользователей при поиске в warehouse не отображается email пользователя. Однако, прежде чем обработчик начнет работу, запрос попадает в [миддлвару InternalOnly](../../services/warehouse/src/auth-server/internal/middleware/auth.go#L52-L60), которая проверяет наличие заголовка `X-Forwarded-Host`. Данный заголовок автоматически выставляется на ingress nginx.

Сделаем краткое резюме:
- на `/users/serach` auth-server возвращает флаги в поле `email`;
- реализуется проверка наличия заголовка `X-Forwarded-Host`.

Теперь перейдем к рассмотрению `gateway-server`. Данный сервис реализует функциональность реверс-прокси. В функции проксирования запросов, есть  [настройка заголовков](../../services/warehouse/src/gateway-server/internal/proxy/handler.go#L142-L146), которая с одной стороны реализует перенос заголовка `Authorization`, но с другой, затирает все остальные заголовки, в том числе и заголовок `X-Forwarded-Host`, за счет которого реализуются гарантии ограничения доступа к `/users/search` на `auth-server`.

Подводя итог, если собрать две уязвимости вместе, то получаем довольно простую реализацию атаки:
1. Создаем virtual service на `gateway-service` с внутренним **k8s** адресом `auth-server` (иными словами название абстракции `Service`, которая обслуживает `Pod` `auth-server`; что-то в духе `http://warehouse-auth-server:8081`);
2. Делаем запрос через `gateway-service` к `/users/search?query=<user-id>` на `auth-server`.

## Как фиксить
Прежде чем приступить к описанию конкретных действий по исправлению уязвимостей, необходимо рассказать о том, как применять патчи в условиях текущей инфраструктуры. 

Текущая инфраструктура построена на базе однонодовой инсталяции [k3s](https://k3s.io/), по сути легковесный аналог [Kubernetes](https://kubernetes.io/). Накатка патчей на сервис сводится к следующим шагам.
1. Произвести изменения в коде (как это всегда и делается);
2. Перейти в папку сервиса: `cd /service/warehouse`
3. Собрать образ Docker с тегом `latest` (`docker build -f utils/docker/<Dockerfile-name> -t warehouse-<service-name>:latest .`);
4. Перезапустить Pod с сервисом (`kubectl delete pod <pod-name>`). В этот момент произойдет удаление пода с сервисом и автоматический запуск нового пода, но образ подхватится новый, из-за тега latest. Такая хитрая механика работает благодаря абстракции Deployment.

Например, для того, чтобы накатить патч на сервис auth-server в warehouse нужно выполнить команды:
```bash
ubuntu@vulnbox-warehouse:~$ cd /service/warehouse

ubuntu@vulnbox-warehouse:/services/warehouse$ sudo docker build -f utils/docker/auth-server.Dockerfile -t warehouse-auth-server:latest .
DEPRECATED: The legacy builder is deprecated and will be removed in a future release.
            Install the buildx component to build images with BuildKit:
            https://docs.docker.com/go/buildx/

Sending build context to Docker daemon  978.9kB
Step 1/21 : FROM node:20-alpine AS frontend-builder
 ---> 9992b59c17bf
 ....
 Step 21/21 : CMD ["./auth-server"]
 ---> Running in 0c5292cdf692
 ---> Removed intermediate container 0c5292cdf692
 ---> 3f30168ad5fc
Successfully built 3f30168ad5fc
Successfully tagged warehouse-auth-server:latest

ubuntu@vulnbox-warehouse:/services/warehouse$ kubectl delete po warehouse-auth-server-557f49c5d8-7ffcs
pod "warehouse-auth-server-557f49c5d8-7ffcs" deleted

ubuntu@vulnbox-warehouse:/services/warehouse$ sleep 10 && kubectl get po
NAME                                                  READY   STATUS    RESTARTS   AGE
warehouse-auth-server-557f49c5d8-jx9t6                1/1     Running   0          11s
```


### Генерация API Key в ti-server
Один из наиболее качественных способов защиты — это использование для генерации API ключа криптостойкие ГПСЧ. Например, можно добавить функцию:
```go
import (
	"crypto/rand"
	"encoding/base64"
)

func generateAPIKey() (string, error) {
	keyBytes := make([]byte, 32)
	_, err := rand.Read(keyBytes)
	if err != nil {
		return "", err
	}
	return base64.URLEncoding.EncodeToString(keyBytes), nil
}
```
И сделать изменения в коде функции [CreateFeed](../../services/warehouse/src/ti-server/internal/storage/postgres.go#L54-L67):
```diff
...
func (s *Storage) CreateFeed(ctx context.Context, name, description string, isPublic bool) (*models.Feed, error) {
	...
	if !isPublic {
-		uuid, err := uuid.NewUUID()
+       apiKey, err := generateAPIKey()
		if err != nil {
			return nil, err
		}
-       apiKeyParam = uuid
+		apiKeyParam = apiKey
	}
...
```
После чего можно пересобрать сервис и уязвимость будет устранена. Однако, в рамках соревнования, наиболее эффективный способ заключается в изменении функции [hash](../../services/warehouse/deploy/chart/templates/configmap-postgres.yaml#L99-L107) в базе `tiserver` в `PostgreSQL` (при этом уязвимый код остается):
```bash
kubectl exec -ti warehouse-postgresql-0 -- psql -U postgres -d tiserver -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE OR REPLACE FUNCTION hash() RETURNS TRIGGER AS \$\$
BEGIN
    IF NEW.api_key IS NOT NULL THEN
        NEW.api_key := md5(encode(gen_random_bytes(16), 'hex'));
    END IF;

    RETURN NEW;
END;
\$\$ LANGUAGE plpgsql;"
```

### SSRF в gateway-server
Качественным закрытием уязвимости станет реализация двух изменений:
1. В функции [SeachUsers](../../services/warehouse/src/auth-server/internal/storage/postgres.go#L217-L255) в `auth-server`:
```diff 
...
func (s *Storage) SearchUsers(ctx context.Context, query string, limit int) ([]*models.User, error) {
	...
	for rows.Next() {
		var user models.User
		err := rows.Scan(&user.ID,
			&user.Username,
-			&user.Email,
			&user.PasswordHash,
			&user.Bio,
			&user.CreatedAt,
			&user.UpdatedAt)
		if err != nil {
			return nil, err
		}
		users = append(users, &user)
	}
...
```
Это предотвратит утечку email.

2. Избавление от `SSRF` в `gateway-service` в [ServeHTTP](../../services/warehouse/src/gateway-server/internal/proxy/handler.go#L135-L147):
```diff
...
	proxy.Director = func(req *http.Request) {
		req.Host = targetURL.Host
		req.URL.Host = targetURL.Host
		req.URL.Scheme = targetURL.Scheme
		req.URL.Path = targetURL.Path
		req.URL.RawQuery = targetURL.RawQuery

-		authHeader := r.Header.Get("Authorization")
-		req.Header = http.Header{}
-		if authHeader != "" {
-			req.Header.Set("Authorization", authHeader)
-		}
+       req.Header.Add("Authorization", req.Header.Get("Authorization"))
	}
...
```
Это позволит избежать удаление заголовка X-Forwarded-Host. 

В целом, для защиты достаточно реализовать один из приведенных выше патчей.

## Сплоит

Ищите в репозитории, в папке [`/sploits/warehouse`](../../sploits/warehouse/).

