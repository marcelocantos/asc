test:
	pytest

bullseye:
	@python3 -m py_compile src/asc/*.py && echo "✓ syntax"
	@test -z "$$(git status --porcelain)" && echo "✓ clean tree" || \
		(echo "✗ dirty tree"; git status --short; exit 1)

.PHONY: test bullseye
