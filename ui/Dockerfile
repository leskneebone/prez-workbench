ARG NODE_VERSION=26.5.0
FROM node:${NODE_VERSION}-alpine AS build
ARG NUXT_PUBLIC_PREZ_API_ENDPOINT=http://localhost:8000
ARG NUXT_PUBLIC_PREZ_AUTO_DETECT_HTML=true
ARG NUXT_PUBLIC_PREZ_AUTO_DETECT_MARKDOWN=true
WORKDIR /app
ENV PNPM_HOME="/pnpm" PATH="$PNPM_HOME:$PATH"
RUN npm install -g corepack && corepack enable
ARG PREZ_UI_VERSION=4.3.3
RUN pnpm dlx create-prez-app@${PREZ_UI_VERSION} prez-ui
WORKDIR /app/prez-ui
RUN pnpm add -D prez-ui@${PREZ_UI_VERSION} \
  --allow-build='@fortawesome/fontawesome-common-types' \
  --allow-build='@fortawesome/free-solid-svg-icons' \
  --allow-build=esbuild \
  --allow-build=prez-components \
  --allow-build=prez-lib \
  --allow-build=prez-ui \
  --allow-build=vue-demi
RUN pnpm add ol@10.10.0
RUN pnpm install
RUN npm --platform=linux --arch=x64 --libc=musl rebuild sharp
COPY components/ItemTable.vue app/components/ItemTable.vue
COPY components/Map.vue app/components/Map.vue
COPY components/ATNSReferenceDetails.vue app/components/ATNSReferenceDetails.vue
COPY components/ATNSSpatialCoverageDetails.vue app/components/ATNSSpatialCoverageDetails.vue
COPY components/ODRLAgreementDetails.vue app/components/ODRLAgreementDetails.vue
COPY components/RiCOInstantiationDetails.vue app/components/RiCOInstantiationDetails.vue
ENV NUXT_PUBLIC_PREZ_API_ENDPOINT=$NUXT_PUBLIC_PREZ_API_ENDPOINT \
    NUXT_PUBLIC_PREZ_AUTO_DETECT_HTML=$NUXT_PUBLIC_PREZ_AUTO_DETECT_HTML \
    NUXT_PUBLIC_PREZ_AUTO_DETECT_MARKDOWN=$NUXT_PUBLIC_PREZ_AUTO_DETECT_MARKDOWN
RUN pnpm generate

FROM nginx:stable-alpine
COPY --from=build /app/prez-ui/.output/public /usr/share/nginx/html
COPY default.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
