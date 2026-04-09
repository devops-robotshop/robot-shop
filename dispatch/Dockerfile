FROM golang:1.21-alpine AS builder

RUN apk add --no-cache git

WORKDIR /app
COPY go.mod ./

RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux go build -o dispatch

FROM gcr.io/distroless/static-debian12

WORKDIR /app

COPY --from=builder /app/dispatch .

EXPOSE 8080

CMD ["./dispatch"]
