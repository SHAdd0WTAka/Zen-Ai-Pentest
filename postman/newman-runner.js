#!/usr/bin/env node
/**
 * Newman Runner for Zen AI Pentest API Tests
 * Runs Postman collections via CLI for CI/CD integration
 */

const newman = require('newman');
const path = require('path');
const fs = require('fs');

// Configuration
const CONFIG = {
  collection: path.join(__dirname, 'Zen-AI-Pentest.postman_collection.json'),
  environments: {
    local: path.join(__dirname, 'Local.postman_environment.json'),
    staging: path.join(__dirname, 'Staging.postman_environment.json'),
    production: path.join(__dirname, 'Production.postman_environment.json')
  },
  reportsDir: path.join(__dirname, 'reports')
};

// Ensure reports directory exists
if (!fs.existsSync(CONFIG.reportsDir)) {
  fs.mkdirSync(CONFIG.reportsDir, { recursive: true });
}

/**
 * Run collection with specified environment
 */
async function runCollection(environment = 'local', options = {}) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const reportPrefix = `report-${environment}-${timestamp}`;
  
  const newmanOptions = {
    collection: CONFIG.collection,
    environment: CONFIG.environments[environment],
    reporters: ['cli', 'htmlextra', 'json', 'junit'],
    reporter: {
      htmlextra: {
        export: path.join(CONFIG.reportsDir, `${reportPrefix}.html`),
        template: path.join(__dirname, 'templates', 'report-template.hbs'),
        showOnlyFails: false,
        skipSensitiveData: true
      },
      json: {
        export: path.join(CONFIG.reportsDir, `${reportPrefix}.json`)
      },
      junit: {
        export: path.join(CONFIG.reportsDir, `${reportPrefix}.xml`)
      }
    },
    insecure: options.insecure || false,
    bail: options.bail !== false, // Stop on first failure by default
    timeout: {
      request: options.timeout || 30000,
      script: options.scriptTimeout || 5000
    },
    iterationCount: options.iterations || 1,
    delayRequest: options.delay || 100
  };

  // Add globals if provided
  if (options.globals) {
    newmanOptions.globals = options.globals;
  }

  return new Promise((resolve, reject) => {
    console.log(`\n🚀 Running collection with ${environment} environment...\n`);

    newman.run(newmanOptions, function (err, summary) {
      if (err) {
        console.error('\n❌ Collection run error:', err);
        reject(err);
        return;
      }

      // Print summary
      console.log('\n📊 Test Summary:');
      console.log('================');
      console.log(`Total Requests: ${summary.run.stats.requests.total}`);
      console.log(`Failed Requests: ${summary.run.stats.requests.failed}`);
      console.log(`Total Tests: ${summary.run.stats.tests.total}`);
      console.log(`Failed Tests: ${summary.run.stats.tests.failed}`);
      console.log(`Total Assertions: ${summary.run.stats.assertions.total}`);
      console.log(`Failed Assertions: ${summary.run.stats.assertions.failed}`);
      console.log(`Average Response Time: ${summary.run.timings.responseAverage}ms`);

      // Check for failures
      if (summary.run.failures.length > 0) {
        console.log('\n❌ Failures:');
        summary.run.failures.forEach((failure, index) => {
          console.log(`  ${index + 1}. ${failure.source.name || failure.source.id}`);
          console.log(`     Error: ${failure.error.message}`);
        });
      }

      // Export summary
      const summaryPath = path.join(CONFIG.reportsDir, `${reportPrefix}-summary.json`);
      fs.writeFileSync(summaryPath, JSON.stringify({
        environment,
        timestamp: new Date().toISOString(),
        stats: summary.run.stats,
        timings: summary.run.timings,
        failures: summary.run.failures.length,
        reports: {
          html: `${reportPrefix}.html`,
          json: `${reportPrefix}.json`,
          junit: `${reportPrefix}.xml`
        }
      }, null, 2));

      console.log(`\n📄 Reports saved to: ${CONFIG.reportsDir}`);
      console.log(`   Summary: ${summaryPath}`);

      // Exit with appropriate code
      if (summary.run.failures.length > 0) {
        reject(new Error(`${summary.run.failures.length} test(s) failed`));
      } else {
        console.log('\n✅ All tests passed!');
        resolve(summary);
      }
    });
  });
}

/**
 * Run specific folder from collection
 */
async function runFolder(folderName, environment = 'local') {
  const newmanOptions = {
    collection: CONFIG.collection,
    environment: CONFIG.environments[environment],
    folder: folderName,
    reporters: ['cli'],
    bail: false
  };

  return new Promise((resolve, reject) => {
    console.log(`\n🚀 Running folder '${folderName}'...\n`);

    newman.run(newmanOptions, function (err, summary) {
      if (err) {
        reject(err);
        return;
      }
      resolve(summary);
    });
  });
}

/**
 * Run health check only
 */
async function runHealthCheck(environment = 'local') {
  return runFolder('Health & Status', environment);
}

// CLI interface
if (require.main === module) {
  const args = process.argv.slice(2);
  const command = args[0] || 'run';
  const environment = args[1] || 'local';

  switch (command) {
    case 'run':
      runCollection(environment)
        .then(() => process.exit(0))
        .catch(() => process.exit(1));
      break;

    case 'health':
      runHealthCheck(environment)
        .then(() => process.exit(0))
        .catch(() => process.exit(1));
      break;

    case 'folder':
      const folderName = args[2];
      if (!folderName) {
        console.error('❌ Please specify a folder name');
        process.exit(1);
      }
      runFolder(folderName, environment)
        .then(() => process.exit(0))
        .catch(() => process.exit(1));
      break;

    case 'list':
      const collection = JSON.parse(fs.readFileSync(CONFIG.collection, 'utf8'));
      console.log('\n📁 Available Folders:');
      collection.item.forEach((folder, index) => {
        console.log(`  ${index + 1}. ${folder.name}`);
        console.log(`     ${folder.item?.length || 0} requests`);
      });
      break;

    case 'help':
    default:
      console.log(`
Zen AI Pentest - Newman Runner

Usage:
  node newman-runner.js [command] [environment] [options]

Commands:
  run [env]           Run full collection (default)
  health [env]        Run health checks only
  folder [env] [name] Run specific folder
  list                List available folders
  help                Show this help

Environments:
  local     (default)  http://localhost:8000
  staging              Staging environment
  production           Production environment

Examples:
  node newman-runner.js
  node newman-runner.js run local
  node newman-runner.js health staging
  node newman-runner.js folder local "Authentication"
  node newman-runner.js list
      `);
      process.exit(0);
  }
}

module.exports = {
  runCollection,
  runFolder,
  runHealthCheck,
  CONFIG
};
