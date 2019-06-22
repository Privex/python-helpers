# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Automatically rebuild Sphinx docs on source code changes
live: 
	sphinx-autobuild --port 8100 -z .. -b html "$(SOURCEDIR)" $(SPHINXOPTS) "$(BUILDDIR)/html"

# Generate API docs in source/code, making sure to exclude setup.py, dist, build, and egg info etc.
rst:
	sphinx-apidoc -o "$(SOURCEDIR)/code/" ../ ../setup.py ../dist ../build ../privex_helpers.egg-info '**__pycache__**'

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
