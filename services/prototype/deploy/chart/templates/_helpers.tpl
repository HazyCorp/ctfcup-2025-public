{{- define "prototype.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "prototype.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "prototype.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "prototype.labels" -}}
helm.sh/chart: {{ include "prototype.chart" . }}
{{ include "prototype.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "prototype.selectorLabels" -}}
app.kubernetes.io/name: {{ include "prototype.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "prototype.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "prototype.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{- define "prototype.s3.fullname" -}}
{{- printf "%s-s3" (include "prototype.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "prototype.s3.rootUser" -}}
{{- $secret := (lookup "v1" "Secret" .Release.Namespace (printf "%s-s3-secret" (include "prototype.fullname" .))) -}}
{{- if $secret -}}
{{- index $secret.data "rootUser" | b64dec -}}
{{- else if .Values.s3.rootUser -}}
{{- .Values.s3.rootUser -}}
{{- else -}}
{{- randAlphaNum 20 -}}
{{- end -}}
{{- end -}}

{{- define "prototype.s3.rootPassword" -}}
{{- $secret := (lookup "v1" "Secret" .Release.Namespace (printf "%s-s3-secret" (include "prototype.fullname" .))) -}}
{{- if $secret -}}
{{- index $secret.data "rootPassword" | b64dec -}}
{{- else if .Values.s3.rootPassword -}}
{{- .Values.s3.rootPassword -}}
{{- else -}}
{{- randAlphaNum 32 -}}
{{- end -}}
{{- end -}}

