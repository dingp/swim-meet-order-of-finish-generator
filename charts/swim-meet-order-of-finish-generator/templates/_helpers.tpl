{{/*
Expand the chart name.
*/}}
{{- define "swim-meet-order-of-finish-generator.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified name.
*/}}
{{- define "swim-meet-order-of-finish-generator.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "swim-meet-order-of-finish-generator.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "swim-meet-order-of-finish-generator.selectorLabels" -}}
app.kubernetes.io/name: {{ include "swim-meet-order-of-finish-generator.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "swim-meet-order-of-finish-generator.labels" -}}
helm.sh/chart: {{ include "swim-meet-order-of-finish-generator.chart" . }}
{{ include "swim-meet-order-of-finish-generator.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "swim-meet-order-of-finish-generator.serviceName" -}}
{{- printf "%s" (include "swim-meet-order-of-finish-generator.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "swim-meet-order-of-finish-generator.acmeWebsrvName" -}}
{{- if .Values.tlsAcme.webServer.existing -}}
{{- .Values.tlsAcme.webServer.deploymentName | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-acme-websrv" (include "swim-meet-order-of-finish-generator.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "swim-meet-order-of-finish-generator.acmeServiceName" -}}
{{- if .Values.tlsAcme.webServer.existing -}}
{{- default .Values.tlsAcme.webServer.deploymentName .Values.tlsAcme.webServer.serviceName | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- include "swim-meet-order-of-finish-generator.acmeWebsrvName" . -}}
{{- end -}}
{{- end -}}

{{- define "swim-meet-order-of-finish-generator.acmeClaimName" -}}
{{- if .Values.tlsAcme.webServer.existing -}}
{{- .Values.tlsAcme.webServer.claimName | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-acme-webroot" (include "swim-meet-order-of-finish-generator.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "swim-meet-order-of-finish-generator.ingressHosts" -}}
{{- $hosts := list -}}
{{- range .Values.ingress.userDomains -}}
{{- $hosts = append $hosts . -}}
{{- end -}}
{{- if .Values.ingress.spinDomain -}}
{{- $hosts = append $hosts .Values.ingress.spinDomain -}}
{{- end -}}
{{- toYaml $hosts -}}
{{- end -}}

{{- define "swim-meet-order-of-finish-generator.tlsHosts" -}}
{{- $hosts := .Values.ingress.tls.hosts | default .Values.ingress.userDomains -}}
{{- toYaml $hosts -}}
{{- end -}}

{{- define "swim-meet-order-of-finish-generator.image" -}}
{{- printf "%s:%s" .Values.image.repository (.Values.image.tag | default .Chart.AppVersion) -}}
{{- end -}}

{{- define "swim-meet-order-of-finish-generator.acmeImage" -}}
{{- printf "%s:%s" .Values.tlsAcme.image.repository (.Values.tlsAcme.image.tag | default .Chart.AppVersion) -}}
{{- end -}}

{{- define "swim-meet-order-of-finish-generator.gen-certs" -}}
{{- $altNames := list -}}
{{- range .Values.ingress.userDomains -}}
{{- $altNames = append $altNames . -}}
{{- end -}}
{{- if .Values.ingress.spinDomain -}}
{{- $altNames = append $altNames .Values.ingress.spinDomain -}}
{{- end -}}
{{- $ca := genCA "swim-meet-order-of-finish-generator-placeholder-ca" 365 -}}
{{- $cert := genSignedCert (first $altNames | default "placeholder.invalid") nil $altNames 365 $ca -}}
tls.crt: {{ $cert.Cert | b64enc }}
tls.key: {{ $cert.Key | b64enc }}
{{- end -}}
