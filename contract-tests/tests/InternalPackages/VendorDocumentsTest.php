<?php

declare(strict_types=1);

namespace ContractTests\Tests\InternalPackages;

use ContractTests\Attribute\ContractTest;
use ContractTests\CallsContractTestCase;

/**
 * Tests that vendor package files appear as SCIP documents when configured as internal.
 *
 * When symfony/messenger is configured in scip-php.json as an internal package,
 * its PHP files should be indexed alongside project files.
 *
 * Requires: bin/run.sh test --internal
 */
class VendorDocumentsTest extends CallsContractTestCase
{
    /**
     * Vendor documents from symfony/messenger should appear in the index.
     *
     * Code reference: vendor/symfony/messenger/ (entire package)
     */
    #[ContractTest(
        name: 'Vendor Documents Exist',
        description: 'When symfony/messenger is internal, its PHP files appear as SCIP documents with vendor/ prefix in relative_path',
        category: 'internal',
        internal: true,
    )]
    public function testVendorDocumentsExist(): void
    {
        $this->requireScipData();

        $vendorDocs = array_filter(
            $this->scipData()->filePaths(),
            fn(string $path) => str_contains($path, 'vendor/') && str_contains($path, 'messenger'),
        );

        $this->assertNotEmpty(
            $vendorDocs,
            'Internal package symfony/messenger should have vendor documents in the index',
        );
        $this->assertGreaterThan(
            50,
            count($vendorDocs),
            'symfony/messenger should contribute at least 50 vendor documents',
        );
    }

    /**
     * MessageBusInterface.php should be indexed as a document.
     *
     * Code reference: vendor/symfony/messenger/MessageBusInterface.php
     */
    #[ContractTest(
        name: 'MessageBusInterface Document Exists',
        description: 'The core MessageBusInterface.php from symfony/messenger appears as an indexed document with symbol definitions',
        category: 'internal',
        internal: true,
    )]
    public function testMessageBusInterfaceDocumentExists(): void
    {
        $this->requireScipData();

        $found = false;
        foreach ($this->scipData()->filePaths() as $path) {
            if (str_contains($path, 'MessageBusInterface.php')) {
                $found = true;
                $doc = $this->scipData()->getDocumentByPath($path);
                $this->assertNotEmpty(
                    $doc['symbols'] ?? [],
                    'MessageBusInterface document should have symbol definitions',
                );
                break;
            }
        }

        $this->assertTrue($found, 'MessageBusInterface.php should be in the index as a vendor document');
    }

    /**
     * Envelope.php (a core class with many methods) should be indexed.
     *
     * Code reference: vendor/symfony/messenger/Envelope.php
     */
    #[ContractTest(
        name: 'Envelope Document Has Symbols',
        description: 'Envelope.php from symfony/messenger is indexed with multiple symbol definitions (class, methods, properties)',
        category: 'internal',
        internal: true,
    )]
    public function testEnvelopeDocumentHasSymbols(): void
    {
        $this->requireScipData();

        $found = false;
        foreach ($this->scipData()->filePaths() as $path) {
            if (str_ends_with($path, 'Envelope.php') && str_contains($path, 'messenger')) {
                $found = true;
                $doc = $this->scipData()->getDocumentByPath($path);
                $this->assertGreaterThan(
                    10,
                    count($doc['symbols'] ?? []),
                    'Envelope.php should have many symbol definitions (class, methods, properties)',
                );
                break;
            }
        }

        $this->assertTrue($found, 'Envelope.php should be in the index');
    }

    /**
     * Project documents (src/) should still be present alongside vendor docs.
     */
    #[ContractTest(
        name: 'Project Documents Still Present',
        description: 'Adding internal packages does not remove project documents — src/ files are still indexed',
        category: 'internal',
        internal: true,
    )]
    public function testProjectDocumentsStillPresent(): void
    {
        $this->requireScipData();

        $projectDocs = array_filter(
            $this->scipData()->filePaths(),
            fn(string $path) => str_starts_with($path, 'src/'),
        );

        $this->assertCount(
            30,
            $projectDocs,
            'All 30 project documents should still be present',
        );
    }

    /**
     * Total document count should exceed baseline when internal package is added.
     */
    #[ContractTest(
        name: 'Document Count Exceeds Baseline',
        description: 'With symfony/messenger as internal, total document count exceeds the baseline 30 project documents',
        category: 'internal',
        internal: true,
    )]
    public function testDocumentCountExceedsBaseline(): void
    {
        $this->requireScipData();

        $this->assertGreaterThan(
            30,
            $this->scipData()->documentCount(),
            'Total documents should exceed baseline 30 when internal package is configured',
        );
    }
}
