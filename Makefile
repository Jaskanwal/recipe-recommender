# Reference https://github.com/hackalog/make_better_defaults/tree/main
include Makefile.include
include Makefile.envs
include Makefile.help

.PHONY: clean
## Delete all compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -f .make.*

.PHONY: run_qdrant
## Run Qdrant docker image
run_qdrant:
	docker pull qdrant/qdrant
	docker run -p 6333:6333 -p 6334:6334 \
    -v $(DATA_DIR)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant
