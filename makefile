all: clear run

clear:
	@docker compose down
	@docker compose rm

build:
	@docker compose build

run: build
	@docker compose up -d
