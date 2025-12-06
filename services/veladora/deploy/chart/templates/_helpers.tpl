{{/*
Expand the name of the chart.
*/}}
{{- define "veladora.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "veladora.fullname" -}}
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

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "veladora.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "veladora.labels" -}}
helm.sh/chart: {{ include "veladora.chart" . }}
{{ include "veladora.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "veladora.selectorLabels" -}}
app.kubernetes.io/name: {{ include "veladora.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "veladora.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "veladora.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
PostgreSQL fullname
*/}}
{{- define "veladora.postgres.fullname" -}}
{{- printf "%s-postgres" (include "veladora.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Redis fullname
*/}}
{{- define "veladora.redis.fullname" -}}
{{- printf "%s-redis" (include "veladora.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Frontend fullname
*/}}
{{- define "veladora.frontend.fullname" -}}
{{- printf "%s-frontend" (include "veladora.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Generate PostgreSQL user
*/}}
{{- define "veladora.postgres.user" -}}
{{- $secret := (lookup "v1" "Secret" .Release.Namespace (printf "%s-postgres-secret" (include "veladora.fullname" .))) -}}
{{- if $secret -}}
{{- index $secret.data "user" | b64dec -}}
{{- else if .Values.postgres.user -}}
{{- .Values.postgres.user -}}
{{- else -}}
{{- "postgres" -}}
{{- end -}}
{{- end -}}

{{/*
Generate PostgreSQL password
*/}}
{{- define "veladora.postgres.password" -}}
{{- $secret := (lookup "v1" "Secret" .Release.Namespace (printf "%s-postgres-secret" (include "veladora.fullname" .))) -}}
{{- if $secret -}}
{{- index $secret.data "password" | b64dec -}}
{{- else if .Values.postgres.password -}}
{{- .Values.postgres.password -}}
{{- else -}}
{{- randAlphaNum 32 -}}
{{- end -}}
{{- end -}}

{{/*
Generate Redis password
*/}}
{{- define "veladora.redis.password" -}}
{{- $secret := (lookup "v1" "Secret" .Release.Namespace (printf "%s-redis-secret" (include "veladora.fullname" .))) -}}
{{- if $secret -}}
{{- index $secret.data "password" | b64dec -}}
{{- else if .Values.redis.password -}}
{{- .Values.redis.password -}}
{{- else -}}
{{- "" -}}
{{- end -}}
{{- end -}}

{{/*
Generate JWT secret
*/}}
{{- define "veladora.jwt.secret" -}}
{{- $secret := (lookup "v1" "Secret" .Release.Namespace (printf "%s-jwt-secret" (include "veladora.fullname" .))) -}}
{{- if $secret -}}
{{- index $secret.data "secret" | b64dec -}}
{{- else -}}
{{- randAlphaNum 64 -}}
{{- end -}}
{{- end -}}

