.PHONY: index
index:
	bash scripts/index.sh

.PHONY: test-migrations
test-migrations:
	bash scripts/run_migration_tests.sh

.PHONY: ui-install
ui-install:
	cd app/ui && npm install

.PHONY: ui-dev
ui-dev:
	cd app/ui && npm run dev

.PHONY: ui-build
ui-build:
	cd app/ui && npm run build

.PHONY: ui-preview
ui-preview:
	cd app/ui && npm run preview

.PHONY: ui-test
ui-test:
	cd app/ui && npm test

.PHONY: ui-test-coverage
ui-test-coverage:
	cd app/ui && npm test -- --coverage

.PHONY: ui-lint
ui-lint:
	cd app/ui && npm run lint

.PHONY: ui-lint-fix
ui-lint-fix:
	cd app/ui && npm run lint:fix

.PHONY: ui-deploy
ui-deploy:
	sudo /opt/feature-factory/scripts/deploy_ui.sh

.PHONY: ui-e2e-test
ui-e2e-test:
	cd app/ui && npm run test:e2e

.PHONY: ui-performance-test
ui-performance-test:
	cd app/ui && npm run test:performance

.PHONY: ui-security-test
ui-security-test:
	cd app/ui && npm run test:security

.PHONY: ui-accessibility-test
ui-accessibility-test:
	cd app/ui && npm run test:accessibility

.PHONY: ui-compatibility-test
ui-compatibility-test:
	cd app/ui && npm run test:compatibility