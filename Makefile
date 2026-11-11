.PHONY: verify shellcheck safety

verify: shellcheck safety

shellcheck:
	@find scripts -type f \( -name '*.sh' -o -name '10-start-zuk-ha-core' \) -print0 | xargs -0 -n1 bash -n
	@echo 'Shell syntax: OK'

safety:
	@python3 tests/check_public_repo.py
	@git diff --check
	@echo 'Public content audit: OK'
