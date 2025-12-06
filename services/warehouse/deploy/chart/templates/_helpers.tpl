{{/*
Expand the name of the chart.
*/}}
{{- define "warehouse.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "warehouse.fullname" -}}
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
{{- define "warehouse.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "warehouse.labels" -}}
helm.sh/chart: {{ include "warehouse.chart" . }}
{{ include "warehouse.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "warehouse.selectorLabels" -}}
app.kubernetes.io/name: {{ include "warehouse.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Component specific labels
*/}}
{{- define "warehouse.componentLabels" -}}
{{- $component := .component -}}
{{- $context := .context -}}
{{ include "warehouse.labels" $context }}
app.kubernetes.io/component: {{ $component }}
{{- end }}

{{/*
Component specific selector labels
*/}}
{{- define "warehouse.componentSelectorLabels" -}}
{{- $component := .component -}}
{{- $context := .context -}}
{{ include "warehouse.selectorLabels" $context }}
app.kubernetes.io/component: {{ $component }}
{{- end }}

{{/*
PostgreSQL fullname
*/}}
{{- define "warehouse.postgresql.fullname" -}}
{{- printf "%s-postgresql" (include "warehouse.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
PostgreSQL service name
*/}}
{{- define "warehouse.postgresql.serviceName" -}}
{{- if .Values.postgresql.enabled }}
{{- include "warehouse.postgresql.fullname" . }}
{{- else }}
{{- .Values.postgresql.externalHost }}
{{- end }}
{{- end }}

{{/*
Generate random password
*/}}
{{- define "warehouse.password" -}}
{{- $secret := lookup "v1" "Secret" .Release.Namespace .secretName -}}
{{- if $secret -}}
{{- index $secret.data .key | b64dec -}}
{{- else -}}
{{- randAlphaNum 32 -}}
{{- end -}}
{{- end -}}

{{/*
TI Server fullname
*/}}
{{- define "warehouse.tiServer.fullname" -}}
{{- printf "%s-ti-server" (include "warehouse.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Auth Server fullname
*/}}
{{- define "warehouse.authServer.fullname" -}}
{{- printf "%s-auth-server" (include "warehouse.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Warehouse fullname
*/}}
{{- define "warehouse.warehouse.fullname" -}}
{{- printf "%s-warehouse" (include "warehouse.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Gateway Server fullname
*/}}
{{- define "warehouse.gatewayServer.fullname" -}}
{{- printf "%s-gateway-server" (include "warehouse.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Image name helper
*/}}
{{- define "warehouse.image" -}}
{{- $registry := .registry -}}
{{- $repository := .repository -}}
{{- $tag := .tag -}}
{{- if $registry -}}
{{- printf "%s/%s:%s" $registry $repository $tag -}}
{{- else -}}
{{- printf "%s:%s" $repository $tag -}}
{{- end -}}
{{- end -}}

{{/*
Create the name of the service account to use
*/}}
{{- define "warehouse.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "warehouse.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Generate secrets names
*/}}
{{- define "warehouse.secretName.postgres" -}}
{{- printf "%s-postgres-secret" (include "warehouse.fullname" .) }}
{{- end }}

{{- define "warehouse.secretName.tiServer" -}}
{{- printf "%s-ti-server-secret" (include "warehouse.fullname" .) }}
{{- end }}

{{- define "warehouse.secretName.authServer" -}}
{{- printf "%s-auth-server-secret" (include "warehouse.fullname" .) }}
{{- end }}

{{- define "warehouse.secretName.warehouse" -}}
{{- printf "%s-warehouse-secret" (include "warehouse.fullname" .) }}
{{- end }}

{{- define "warehouse.secretName.gatewayServer" -}}
{{- printf "%s-gateway-server-secret" (include "warehouse.fullname" .) }}
{{- end }}
