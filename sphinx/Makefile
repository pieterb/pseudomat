.PHONY: apidoc server clean invclean gh-pages

RM            := rm -rf
SPHINXOPTS    := -d .doctrees
SPHINXBUILD   := sphinx-build
SPHINXAPIDOC  := sphinx-apidoc
AUTOBUILD     := sphinx-autobuild
SOURCEDIR     := ..
BUILDDIR      := build
GITORIGIN     = "$$(git remote show -n origin | grep 'Fetch URL:' | grep -o 'git@.*')"
GITBRANCH     := $(shell git branch | grep '^\* ' | sed 's/^\* //')


apidoc: clean
	$(SPHINXAPIDOC) --force --module-first --no-toc --private -o "./apidoc" "../" sphinx


build:
	$(SPHINXBUILD) -b html . "$(BUILDDIR)" $(SPHINXOPTS)


server:
	@$(AUTOBUILD) . "$(BUILDDIR)" $(SPHINXOPTS) --watch "$(SOURCEDIR)" --ignore build


clean:
	@$(RM) $(BUILDDIR) .doctrees apidoc


invclean:
	@$(RM) *.inv *.inv.txt


gh-pages: build
	[ -d gh-pages ] || git clone --branch gh-pages --depth 1 $(GITORIGIN) gh-pages
	cd gh-pages && { [ "`echo *`" = '*' ] || git rm -rf *; }
	cd build && cp -a * ../gh-pages
	cd gh-pages && \
	  git add * && \
	  git commit -m "Update from branch $(GITBRANCH)" && \
	  git push
	cd ..
	rm -rf gh-pages
