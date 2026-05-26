# udi-poly-ELK — XML validation and PG3 release artifacts (tag + per-track zips).
#
# PG3 release flow (clean tree; not detached HEAD):
#   1. Bump nodes/__init__.py VERSION and profile/version.txt; commit.
#   2. `make release`     — tag v<VERSION> and push current branch + tag.
#                           Then in PG3 UI, edit the plugin and set Version to that exact VERSION.
#   3. `make beta`        — push HEAD to the `beta` branch (reference) and build $(NAME)-beta-<VERSION>.zip.
#                           Then in PG3 UI, edit the plugin and set Version to that exact VERSION.
#   4. `make production`  — push HEAD to the `production` branch (reference) and build $(NAME)-production-<VERSION>.zip.
# The track-specific zip files are the actual deliverables uploaded to PG3.

PYTHON ?= python3
NAME = ELK
GIT_REMOTE ?= origin
BRANCH_BETA ?= beta
BRANCH_PRODUCTION ?= production
XML_FILES = profile/*/*.xml

# sudo apt-get install libxml2-utils libxml2-dev
check: xml-check

xml-check:
	xmllint --noout $(XML_FILES)

help:
	@echo "Quality"
	@echo "  make check / xml-check   Validate profile XML"
	@echo ""
	@echo "PG3 release (clean tree; not detached HEAD)"
	@echo "  make release             Tag v\$$VERSION and push current branch + tag"
	@echo "  make beta                Push HEAD -> $(GIT_REMOTE)/$(BRANCH_BETA) and build $(NAME)-$(BRANCH_BETA)-\$$VERSION.zip"
	@echo "  make production          Push HEAD -> $(GIT_REMOTE)/$(BRANCH_PRODUCTION) and build $(NAME)-$(BRANCH_PRODUCTION)-\$$VERSION.zip"
	@echo "                           After make release / make beta / make production, edit plugin in PG3 UI and set Version to \$$VERSION"
	@echo "  make zip                 Ad-hoc local $(NAME).zip (no version suffix)"
	@echo ""
	@echo "Variables: PYTHON GIT_REMOTE BRANCH_BETA BRANCH_PRODUCTION"

clean:
	$(PYTHON) -c "import pathlib, shutil; r = pathlib.Path('.'); [shutil.rmtree(p, ignore_errors=True) for p in r.rglob('__pycache__') if p.is_dir()]; shutil.rmtree('.pytest_cache', ignore_errors=True)"
	rm -f $(NAME)*.zip

# Ad-hoc local archive (no version suffix). For PG3 uploads, prefer `make beta` / `make production`.
zip:
	rm -f $(NAME).zip
	zip -x@zip_exclude.lst -r $(NAME).zip *

# Push current HEAD to $(GIT_REMOTE)/$(BRANCH_BETA) (reference) and build $(NAME)-$(BRANCH_BETA)-<VERSION>.zip
# for upload to PG3. Requires clean tree; not detached HEAD.
beta:
	@set -e; \
	ROOT=$$(pwd); \
	VERSION=$$(sed -n 's/^VERSION = "\([^"]*\)"$$/\1/p' "$$ROOT/nodes/__init__.py"); \
	test -n "$$VERSION" || { echo "Could not parse VERSION from $$ROOT/nodes/__init__.py"; exit 1; }; \
	test -z "$$(git -C "$$ROOT" status --porcelain)" || { \
		echo "Working tree is not clean. Commit or stash before make beta."; \
		git -C "$$ROOT" status --short; \
		exit 1; \
	}; \
	BRANCH=$$(git -C "$$ROOT" rev-parse --abbrev-ref HEAD); \
	if [ "$$BRANCH" = "HEAD" ]; then \
		echo "ERROR: detached HEAD. Checkout a branch, then run make beta."; \
		exit 1; \
	fi; \
	REPO=$$(git -C "$$ROOT" rev-parse --show-toplevel); \
	git -C "$$ROOT" push "$(GIT_REMOTE)" HEAD:"$(BRANCH_BETA)"; \
	echo "Repository: $$REPO"; \
	echo "Branch: $(BRANCH_BETA)"; \
	echo "Pushed $$(git -C "$$ROOT" rev-parse --short HEAD) to $(GIT_REMOTE)/$(BRANCH_BETA)."; \
	ZIPFILE="$(NAME)-$(BRANCH_BETA)-$$VERSION.zip"; \
	rm -f "$$ZIPFILE"; \
	zip -x@zip_exclude.lst -r "$$ZIPFILE" * >/dev/null; \
	echo "Built $$ROOT/$$ZIPFILE for upload to PG3."; \
	echo "PG3 UI action required: edit this plugin and set Version to $$VERSION."

# Push current HEAD to $(GIT_REMOTE)/$(BRANCH_PRODUCTION) (reference) and build $(NAME)-$(BRANCH_PRODUCTION)-<VERSION>.zip
# for upload to PG3. Requires clean tree; not detached HEAD.
production:
	@set -e; \
	ROOT=$$(pwd); \
	VERSION=$$(sed -n 's/^VERSION = "\([^"]*\)"$$/\1/p' "$$ROOT/nodes/__init__.py"); \
	test -n "$$VERSION" || { echo "Could not parse VERSION from $$ROOT/nodes/__init__.py"; exit 1; }; \
	test -z "$$(git -C "$$ROOT" status --porcelain)" || { \
		echo "Working tree is not clean. Commit or stash before make production."; \
		git -C "$$ROOT" status --short; \
		exit 1; \
	}; \
	BRANCH=$$(git -C "$$ROOT" rev-parse --abbrev-ref HEAD); \
	if [ "$$BRANCH" = "HEAD" ]; then \
		echo "ERROR: detached HEAD. Checkout a branch, then run make production."; \
		exit 1; \
	fi; \
	REPO=$$(git -C "$$ROOT" rev-parse --show-toplevel); \
	git -C "$$ROOT" push "$(GIT_REMOTE)" HEAD:"$(BRANCH_PRODUCTION)"; \
	echo "Repository: $$REPO"; \
	echo "Branch: $(BRANCH_PRODUCTION)"; \
	echo "Pushed $$(git -C "$$ROOT" rev-parse --short HEAD) to $(GIT_REMOTE)/$(BRANCH_PRODUCTION)."; \
	ZIPFILE="$(NAME)-$(BRANCH_PRODUCTION)-$$VERSION.zip"; \
	rm -f "$$ZIPFILE"; \
	zip -x@zip_exclude.lst -r "$$ZIPFILE" * >/dev/null; \
	echo "Built $$ROOT/$$ZIPFILE for upload to PG3."; \
	echo "PG3 UI action required: edit this plugin and set Version to $$VERSION."

# Tag the current HEAD as v<VERSION> and push the current branch + tag to $(GIT_REMOTE).
# VERSION = nodes/__init__.py VERSION (canonical). Track-specific zips are built by `make beta` / `make production`.
# Run from this directory, or: make -C /path/to/udi-poly-ELK release
# Requires clean git working tree and a checked-out branch (not detached HEAD).
release:
	@set -e; \
	ROOT=$$(pwd); \
	VERSION=$$(sed -n 's/^VERSION = "\([^"]*\)"$$/\1/p' "$$ROOT/nodes/__init__.py"); \
	test -n "$$VERSION" || { echo "Could not parse VERSION from $$ROOT/nodes/__init__.py"; exit 1; }; \
	test -z "$$(git -C "$$ROOT" status --porcelain)" || { \
		echo "Working tree is not clean. Commit or stash before make release."; \
		git -C "$$ROOT" status --short; \
		exit 1; \
	}; \
	BRANCH=$$(git -C "$$ROOT" rev-parse --abbrev-ref HEAD); \
	if [ "$$BRANCH" = "HEAD" ]; then \
		echo "ERROR: detached HEAD. Checkout your release branch (e.g. master), then run make release."; \
		exit 1; \
	fi; \
	if git -C "$$ROOT" rev-parse -q --verify "refs/tags/v$$VERSION" >/dev/null 2>&1; then \
		echo "Tag v$$VERSION already exists. Delete: git -C \"$$ROOT\" tag -d v$$VERSION"; \
		exit 1; \
	fi; \
	git -C "$$ROOT" tag -a "v$$VERSION" -m "Release $$VERSION"; \
	echo "Created annotated tag v$$VERSION."; \
	git -C "$$ROOT" push "$(GIT_REMOTE)" "$$BRANCH" "v$$VERSION"; \
	echo "Pushed $$BRANCH and v$$VERSION to $(GIT_REMOTE)."; \
	echo "PG3 UI action required: edit this plugin and set Version to $$VERSION."

.PHONY: check xml-check help clean zip beta production release
