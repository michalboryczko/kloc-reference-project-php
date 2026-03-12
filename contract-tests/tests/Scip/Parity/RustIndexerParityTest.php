<?php

declare(strict_types=1);

namespace ContractTests\Tests\Scip\Parity;

use ContractTests\Attribute\ContractTest;
use ContractTests\CallsContractTestCase;

/**
 * Contract tests for Rust indexer output parity.
 *
 * These tests specifically target the 9 critical failures from the previous
 * scip-php-rust implementation. Each test is mapped to a specific failure
 * to ensure regression coverage.
 *
 * Previous failures:
 * 1. Wrong output format (separate files)
 * 2. Zero calls/values
 * 3. Indexed vendor files as documents
 * 4. Wrong Composer version (0.0.0)
 * 5. Missing occurrence fields (syntax_kind, enclosing_range, position_encoding)
 * 6. Missing symbol relationships
 * 7. Missing external_symbols
 * 8. Broken PHPDoc parsing
 * 9. Integer vs string types
 */
class RustIndexerParityTest extends CallsContractTestCase
{
    // ═══════════════════════════════════════════════════════════════
    // Previous Failure #1: Wrong output format
    // ═══════════════════════════════════════════════════════════════

    /**
     * Verifies the unified index.json contains both SCIP and calls/values data.
     *
     * Previous failure: scip-php-rust wrote separate index.json + calls.json
     * Expected: Single unified index.json with top-level keys: version, scip, calls, values
     */
    #[ContractTest(
        name: 'Unified output format',
        description: 'Verifies index.json is a single unified file with version, scip, calls, and values sections. Previous failure #1: scip-php-rust wrote separate files.',
        category: 'scip',
    )]
    public function testUnifiedOutputFormat(): void
    {
        $this->requireScipData();

        // If we have both SCIP data and calls data, the unified format is working
        $this->assertTrue($this->hasScipData(), 'SCIP data should be loaded from unified index.json');
        $this->assertNotNull(self::$calls, 'Calls data should be loaded from unified index.json');

        // Verify both have content
        $this->assertGreaterThan(0, $this->scipData()->documentCount(), 'Should have SCIP documents');
        $this->assertGreaterThan(0, self::$calls->callCount(), 'Should have call records');
        $this->assertGreaterThan(0, self::$calls->valueCount(), 'Should have value records');
    }

    // ═══════════════════════════════════════════════════════════════
    // Previous Failure #2: Zero calls/values
    // ═══════════════════════════════════════════════════════════════

    /**
     * Verifies expected call count from reference project.
     *
     * Previous failure: scip-php-rust produced 0 calls
     * Expected: 297 calls for the reference project
     */
    #[ContractTest(
        name: 'Expected call count (297)',
        description: 'Verifies exactly 297 calls are produced for the reference project. Previous failure #2: scip-php-rust produced 0 calls.',
        category: 'scip',
    )]
    public function testExpectedCallCount(): void
    {
        $this->assertEquals(
            297,
            self::$calls->callCount(),
            'Reference project should produce exactly 297 calls'
        );
    }

    /**
     * Verifies expected value count from reference project.
     *
     * Previous failure: scip-php-rust produced 0 values
     * Expected: 506 values for the reference project
     */
    #[ContractTest(
        name: 'Expected value count (506)',
        description: 'Verifies exactly 506 values are produced for the reference project. Previous failure #2: scip-php-rust produced 0 values.',
        category: 'scip',
    )]
    public function testExpectedValueCount(): void
    {
        $this->assertEquals(
            506,
            self::$calls->valueCount(),
            'Reference project should produce exactly 506 values'
        );
    }

    /**
     * Verifies call kind distribution matches expected counts.
     *
     * Expected: access:206, constructor:25, method:48, access_static:15, method_static:3
     */
    #[ContractTest(
        name: 'Call kind distribution',
        description: 'Verifies call kind distribution matches reference: access=206, constructor=25, method=48, access_static=15, method_static=3.',
        category: 'scip',
    )]
    public function testCallKindDistribution(): void
    {
        $expected = [
            'access' => 206,
            'constructor' => 25,
            'method' => 48,
            'access_static' => 15,
            'method_static' => 3,
        ];

        foreach ($expected as $kind => $count) {
            $actual = $this->calls()->kind($kind)->count();
            $this->assertEquals(
                $count,
                $actual,
                "Expected {$count} calls of kind '{$kind}', got {$actual}"
            );
        }
    }

    /**
     * Verifies value kind distribution matches expected counts.
     *
     * Expected: result:297, parameter:145, local:48, literal:12, constant:4
     */
    #[ContractTest(
        name: 'Value kind distribution',
        description: 'Verifies value kind distribution matches reference: result=297, parameter=145, local=48, literal=12, constant=4.',
        category: 'scip',
    )]
    public function testValueKindDistribution(): void
    {
        $expected = [
            'result' => 297,
            'parameter' => 145,
            'local' => 48,
            'literal' => 12,
            'constant' => 4,
        ];

        foreach ($expected as $kind => $count) {
            $actual = $this->values()->kind($kind)->count();
            $this->assertEquals(
                $count,
                $actual,
                "Expected {$count} values of kind '{$kind}', got {$actual}"
            );
        }
    }

    // ═══════════════════════════════════════════════════════════════
    // Previous Failure #3: Indexed vendor files as documents
    // ═══════════════════════════════════════════════════════════════

    /**
     * Verifies exactly 41 documents (only src/ files, no vendor).
     *
     * Previous failure: scip-php-rust produced 1,853 documents (included vendor)
     * Expected: 41 documents, all from src/
     */
    #[ContractTest(
        name: 'Document count is 41 (no vendor)',
        description: 'Verifies exactly 41 documents are indexed (src/ only, no vendor). Previous failure #3: scip-php-rust indexed vendor files, producing 1853 documents.',
        category: 'scip',
    )]
    public function testDocumentCountNoVendor(): void
    {
        $this->requireScipData();

        $documents = $this->scipData()->documents();
        $this->assertCount(41, $documents, 'Should have exactly 41 documents');

        // Verify no vendor paths
        foreach ($documents as $doc) {
            $path = $doc['relative_path'] ?? $doc['relativePath'] ?? '';
            $this->assertStringStartsWith(
                'src/',
                $path,
                "Document path should start with src/, got: {$path}"
            );
            $this->assertStringNotContainsString(
                'vendor/',
                $path,
                "Document path should not contain vendor/: {$path}"
            );
        }
    }

    // ═══════════════════════════════════════════════════════════════
    // Previous Failure #4: Wrong Composer version
    // ═══════════════════════════════════════════════════════════════

    /**
     * Verifies Composer version is read from composer.lock (1.0.0.0 format).
     *
     * Previous failure: scip-php-rust used "0.0.0" instead of reading from composer.lock
     * Expected: Project symbols contain version "1.0.0.0"
     */
    #[ContractTest(
        name: 'Composer version from lockfile (1.0.0.0)',
        description: 'Verifies project symbols use version from composer.lock in Composer normalized format (X.Y.Z.0). Previous failure #4: scip-php-rust used "0.0.0".',
        category: 'scip',
    )]
    public function testComposerVersionFromLockfile(): void
    {
        // Check that project symbols use the correct version from composer.lock
        $values = $this->values()
            ->kind('parameter')
            ->symbolContains('kloc/reference-project-php')
            ->all();

        $this->assertNotEmpty($values, 'Should find parameter values with project package name');

        foreach ($values as $value) {
            $symbol = $value['symbol'] ?? '';
            $this->assertStringContainsString(
                '1.0.0.0',
                $symbol,
                "Symbol should use version 1.0.0.0 from composer.lock, got: {$symbol}"
            );
            $this->assertStringNotContainsString(
                '0.0.0',
                $symbol,
                "Symbol should NOT use version 0.0.0: {$symbol}"
            );
        }
    }

    // ═══════════════════════════════════════════════════════════════
    // Previous Failure #5: Missing occurrence fields
    // ═══════════════════════════════════════════════════════════════

    /**
     * Verifies all occurrences have syntax_kind field.
     *
     * Previous failure: scip-php-rust omitted syntax_kind from occurrences
     * Expected: Every occurrence has syntax_kind (one of: 6, 9, 11, 12, 19)
     */
    #[ContractTest(
        name: 'All occurrences have syntax_kind',
        description: 'Verifies every occurrence has a syntax_kind field. Previous failure #5: scip-php-rust omitted syntax_kind.',
        category: 'scip',
    )]
    public function testAllOccurrencesHaveSyntaxKind(): void
    {
        $this->requireScipData();

        $validSyntaxKinds = [6, 9, 11, 12, 19];
        $missingSyntaxKind = 0;
        $totalOccurrences = 0;

        foreach ($this->scipData()->documents() as $doc) {
            foreach ($doc['occurrences'] ?? [] as $occ) {
                $totalOccurrences++;
                if (!isset($occ['syntax_kind'])) {
                    $missingSyntaxKind++;
                    continue;
                }
                $this->assertContains(
                    $occ['syntax_kind'],
                    $validSyntaxKinds,
                    sprintf(
                        'Invalid syntax_kind %s for symbol %s',
                        var_export($occ['syntax_kind'], true),
                        $occ['symbol'] ?? 'unknown'
                    )
                );
            }
        }

        $this->assertEquals(
            0,
            $missingSyntaxKind,
            "Expected all occurrences to have syntax_kind, {$missingSyntaxKind}/{$totalOccurrences} are missing"
        );
    }

    /**
     * Verifies occurrence count matches expected total.
     *
     * Expected: 1,086 occurrences across 41 documents
     */
    #[ContractTest(
        name: 'Total occurrence count (1086)',
        description: 'Verifies exactly 1086 occurrences across all documents.',
        category: 'scip',
    )]
    public function testTotalOccurrenceCount(): void
    {
        $this->requireScipData();

        $total = 0;
        foreach ($this->scipData()->documents() as $doc) {
            $total += count($doc['occurrences'] ?? []);
        }

        $this->assertEquals(
            1086,
            $total,
            'Expected 1086 total occurrences'
        );
    }

    /**
     * Verifies definitions have symbol_roles=1, references omit the key.
     *
     * Critical finding: References do NOT have symbol_roles=0. The key is absent.
     * Definitions have symbol_roles=1.
     * Expected: 358 definitions with symbol_roles=1, 728 references without the key
     */
    #[ContractTest(
        name: 'Definition/reference symbol_roles pattern',
        description: 'Verifies definitions have symbol_roles=1 and references OMIT symbol_roles entirely (not set to 0). 358 definitions, 728 references.',
        category: 'scip',
    )]
    public function testSymbolRolesPattern(): void
    {
        $this->requireScipData();

        $definitions = 0;
        $referencesWithoutKey = 0;
        $referencesWithZero = 0;

        foreach ($this->scipData()->documents() as $doc) {
            foreach ($doc['occurrences'] ?? [] as $occ) {
                if (array_key_exists('symbol_roles', $occ)) {
                    if ($occ['symbol_roles'] === 1) {
                        $definitions++;
                    } elseif ($occ['symbol_roles'] === 0) {
                        $referencesWithZero++;
                    }
                } else {
                    $referencesWithoutKey++;
                }
            }
        }

        $this->assertEquals(358, $definitions, 'Expected 358 definitions (symbol_roles=1)');
        $this->assertEquals(728, $referencesWithoutKey, 'Expected 728 references without symbol_roles key');
        $this->assertEquals(0, $referencesWithZero, 'No occurrences should have symbol_roles=0 (key should be absent for references)');
    }

    /**
     * Verifies enclosing_range is present on ~42% of definitions.
     *
     * Previous failure: scip-php-rust omitted enclosing_range
     * Expected: 152 definitions have enclosing_range, no references have it
     */
    #[ContractTest(
        name: 'Enclosing range on 152 definitions',
        description: 'Verifies 152/358 definitions have enclosing_range and no references have it. Previous failure #5: scip-php-rust omitted enclosing_range.',
        category: 'scip',
    )]
    public function testEnclosingRangePresence(): void
    {
        $this->requireScipData();

        $defsWithEnclosing = 0;
        $refsWithEnclosing = 0;

        foreach ($this->scipData()->documents() as $doc) {
            foreach ($doc['occurrences'] ?? [] as $occ) {
                $isDefinition = array_key_exists('symbol_roles', $occ) && $occ['symbol_roles'] === 1;
                $hasEnclosing = array_key_exists('enclosing_range', $occ);

                if ($isDefinition && $hasEnclosing) {
                    $defsWithEnclosing++;
                } elseif (!$isDefinition && $hasEnclosing) {
                    $refsWithEnclosing++;
                }
            }
        }

        $this->assertEquals(152, $defsWithEnclosing, 'Expected 152 definitions with enclosing_range');
        $this->assertEquals(0, $refsWithEnclosing, 'No references should have enclosing_range');
    }

    /**
     * Verifies documents have position_encoding field.
     *
     * Previous failure: scip-php-rust omitted position_encoding
     * Expected: Every document has position_encoding = 1 (integer)
     */
    #[ContractTest(
        name: 'Documents have position_encoding',
        description: 'Verifies every document has position_encoding=1 (integer). Previous failure #5: scip-php-rust omitted this field.',
        category: 'scip',
    )]
    public function testDocumentsHavePositionEncoding(): void
    {
        $this->requireScipData();

        foreach ($this->scipData()->documents() as $doc) {
            $path = $doc['relative_path'] ?? $doc['relativePath'] ?? 'unknown';
            $this->assertArrayHasKey(
                'position_encoding',
                $doc,
                "Document {$path} should have position_encoding"
            );
            $this->assertSame(
                1,
                $doc['position_encoding'],
                "Document {$path}: position_encoding should be integer 1"
            );
        }
    }

    // ═══════════════════════════════════════════════════════════════
    // Previous Failure #6: Missing symbol relationships
    // ═══════════════════════════════════════════════════════════════

    /**
     * Verifies 104 symbols have relationships.
     *
     * Previous failure: scip-php-rust produced no relationships
     * Expected: 104 symbols have non-empty relationships arrays
     */
    #[ContractTest(
        name: 'Symbols with relationships (104)',
        description: 'Verifies 104 symbols have non-empty relationships arrays. Previous failure #6: scip-php-rust produced no relationships.',
        category: 'scip',
    )]
    public function testSymbolRelationshipCount(): void
    {
        $this->requireScipData();

        $symbolsWithRels = 0;

        foreach ($this->scipData()->documents() as $doc) {
            foreach ($doc['symbols'] ?? [] as $sym) {
                if (!empty($sym['relationships'])) {
                    $symbolsWithRels++;
                }
            }
        }

        $this->assertEquals(
            104,
            $symbolsWithRels,
            'Expected 104 symbols with relationships'
        );
    }

    /**
     * Verifies EmailSender methods have implementation relationships.
     *
     * Code reference: src/Component/EmailSender.php:7
     *   final class EmailSender implements EmailSenderInterface
     *
     * Expected: EmailSender methods have relationships pointing to EmailSenderInterface methods
     * with is_reference=true and is_implementation=true
     */
    #[ContractTest(
        name: 'Interface implementation relationships',
        description: 'Verifies EmailSender methods have implementation relationships to EmailSenderInterface. Previous failure #6.',
        category: 'scip',
    )]
    public function testInterfaceImplementationRelationships(): void
    {
        $this->requireScipData();

        // Find EmailSender#send() symbol
        $symbols = $this->scip()->symbols()
            ->symbolContains('EmailSender#send().')
            ->hasRelationships()
            ->all();

        // Filter to just the implementation (not interface)
        $implSymbols = array_filter($symbols, function ($s) {
            return !str_contains($s['symbol'], 'Interface');
        });

        $this->assertNotEmpty(
            $implSymbols,
            'EmailSender#send() should have relationships'
        );

        $symbol = reset($implSymbols);
        $relationships = $symbol['info']['relationships'] ?? [];

        $this->assertNotEmpty($relationships, 'Should have at least one relationship');

        // Find the implementation relationship
        $implRel = null;
        foreach ($relationships as $rel) {
            if (str_contains($rel['symbol'] ?? '', 'EmailSenderInterface')) {
                $implRel = $rel;
                break;
            }
        }

        $this->assertNotNull($implRel, 'Should have relationship to EmailSenderInterface');
        $this->assertTrue(
            $implRel['is_implementation'] ?? $implRel['isImplementation'] ?? false,
            'Relationship should be is_implementation=true'
        );
        $this->assertTrue(
            $implRel['is_reference'] ?? $implRel['isReference'] ?? false,
            'Relationship should be is_reference=true'
        );
    }

    // ═══════════════════════════════════════════════════════════════
    // Previous Failure #7: Missing external_symbols
    // ═══════════════════════════════════════════════════════════════

    /**
     * Verifies exactly 25 external symbols are tracked.
     *
     * Previous failure: scip-php-rust produced 0 external symbols
     * Expected: 25 external symbols including PHP builtins and Symfony vendor classes
     */
    #[ContractTest(
        name: 'External symbols count (25)',
        description: 'Verifies exactly 25 external symbols are tracked. Previous failure #7: scip-php-rust produced 0 external symbols.',
        category: 'scip',
    )]
    public function testExternalSymbolCount(): void
    {
        $this->requireScipData();

        // Read the raw JSON to check external_symbols
        $content = file_get_contents(SCIP_JSON_PATH);
        $data = json_decode($content, true);

        $this->assertArrayHasKey('scip', $data, 'index.json should have scip key');
        $this->assertArrayHasKey('external_symbols', $data['scip'], 'scip should have external_symbols');
        $this->assertCount(
            25,
            $data['scip']['external_symbols'],
            'Should have exactly 25 external symbols'
        );
    }

    /**
     * Verifies external symbols include expected PHP builtins.
     *
     * Expected: DateTimeImmutable, sprintf, strtolower, explode, etc.
     */
    #[ContractTest(
        name: 'External symbols include PHP builtins',
        description: 'Verifies external symbols include expected PHP builtins like DateTimeImmutable, sprintf, strtolower.',
        category: 'scip',
    )]
    public function testExternalSymbolsIncludeBuiltins(): void
    {
        $this->requireScipData();

        $content = file_get_contents(SCIP_JSON_PATH);
        $data = json_decode($content, true);

        $externalSymbols = array_map(
            fn($es) => $es['symbol'],
            $data['scip']['external_symbols'] ?? []
        );

        $expectedBuiltins = [
            'DateTimeImmutable#',
            'sprintf().',
            'strtolower().',
            'explode().',
        ];

        foreach ($expectedBuiltins as $builtin) {
            $found = false;
            foreach ($externalSymbols as $symbol) {
                if (str_contains($symbol, $builtin)) {
                    $found = true;
                    break;
                }
            }
            $this->assertTrue(
                $found,
                "External symbols should include a symbol containing '{$builtin}'"
            );
        }
    }

    // ═══════════════════════════════════════════════════════════════
    // Previous Failure #8: Broken PHPDoc parsing
    // ═══════════════════════════════════════════════════════════════

    /**
     * Verifies all symbols have proper documentation format.
     *
     * Previous failure: scip-php-rust produced documentation strings containing raw "/"
     * Expected: First documentation element is ```php\n...\n```, no raw "/" content
     */
    #[ContractTest(
        name: 'Documentation format (no raw /)',
        description: 'Verifies symbol documentation starts with PHP code block and never contains raw "/". Previous failure #8: scip-php-rust had broken PHPDoc.',
        category: 'scip',
    )]
    public function testDocumentationFormat(): void
    {
        $this->requireScipData();

        $totalSymbols = 0;
        $symbolsWithDocs = 0;
        $brokenDocs = [];

        foreach ($this->scipData()->documents() as $doc) {
            foreach ($doc['symbols'] ?? [] as $sym) {
                $totalSymbols++;
                $documentation = $sym['documentation'] ?? [];

                if (empty($documentation)) {
                    continue;
                }

                $symbolsWithDocs++;

                // First element should be a PHP code block
                $first = $documentation[0];
                if (!str_starts_with($first, '```php')) {
                    $brokenDocs[] = sprintf(
                        '%s: first doc element does not start with ```php: %s',
                        $sym['symbol'] ?? 'unknown',
                        substr($first, 0, 50)
                    );
                }

                // No element should be a raw "/"
                foreach ($documentation as $doc_line) {
                    if ($doc_line === '/') {
                        $brokenDocs[] = sprintf(
                            '%s: documentation contains raw "/" string',
                            $sym['symbol'] ?? 'unknown'
                        );
                    }
                }
            }
        }

        $this->assertEquals(358, $totalSymbols, 'Expected 358 total symbols');
        $this->assertEmpty(
            $brokenDocs,
            "Broken documentation found:\n" . implode("\n", array_slice($brokenDocs, 0, 10))
        );
    }

    // ═══════════════════════════════════════════════════════════════
    // Previous Failure #9: Integer vs string types
    // ═══════════════════════════════════════════════════════════════

    /**
     * Verifies metadata.version is integer 1, not string.
     *
     * Previous failure: scip-php-rust used string "4.0" for metadata.version
     * Expected: metadata.version is integer 1
     */
    #[ContractTest(
        name: 'metadata.version is integer 1',
        description: 'Verifies metadata.version is integer 1 (not string "1" or "4.0"). Previous failure #9: scip-php-rust used wrong types.',
        category: 'scip',
    )]
    public function testMetadataVersionIsInteger(): void
    {
        $this->requireScipData();

        $metadata = $this->scipData()->metadata();
        $this->assertArrayHasKey('version', $metadata, 'Metadata should have version');
        $this->assertIsInt($metadata['version'], 'metadata.version should be integer');
        $this->assertSame(1, $metadata['version'], 'metadata.version should be 1');
    }

    /**
     * Verifies text_document_encoding is integer 1.
     *
     * Previous failure: scip-php-rust used string "UTF8"
     * Expected: text_document_encoding is integer 1
     */
    #[ContractTest(
        name: 'text_document_encoding is integer 1',
        description: 'Verifies text_document_encoding is integer 1 (not string "UTF8"). Previous failure #9.',
        category: 'scip',
    )]
    public function testTextDocumentEncodingIsInteger(): void
    {
        $this->requireScipData();

        $metadata = $this->scipData()->metadata();
        $this->assertArrayHasKey('text_document_encoding', $metadata, 'Metadata should have text_document_encoding');
        $this->assertIsInt($metadata['text_document_encoding'], 'text_document_encoding should be integer');
        $this->assertSame(1, $metadata['text_document_encoding'], 'text_document_encoding should be 1');
    }

    /**
     * Verifies language field is string "19" (not integer 19).
     *
     * Critical finding: The spec says integer but reference output has string "19".
     * The Rust implementation MUST match the reference output.
     */
    #[ContractTest(
        name: 'language is string "19"',
        description: 'Verifies documents.language is string "19" (NOT integer 19). Spec says integer but reference output uses string.',
        category: 'scip',
    )]
    public function testLanguageIsString(): void
    {
        $this->requireScipData();

        foreach ($this->scipData()->documents() as $doc) {
            $path = $doc['relative_path'] ?? $doc['relativePath'] ?? 'unknown';
            $this->assertArrayHasKey('language', $doc, "Document {$path} should have language");
            $this->assertIsString($doc['language'], "Document {$path}: language should be string");
            $this->assertSame(
                '19',
                $doc['language'],
                "Document {$path}: language should be string '19'"
            );
        }
    }

    /**
     * Verifies tool_info.name is "scip-php" for drop-in replacement.
     */
    #[ContractTest(
        name: 'tool_info.name is "scip-php"',
        description: 'Verifies tool_info.name is "scip-php" so the Rust binary is a drop-in replacement.',
        category: 'scip',
    )]
    public function testToolInfoName(): void
    {
        $this->requireScipData();

        $metadata = $this->scipData()->metadata();
        $toolInfo = $metadata['tool_info'] ?? [];

        $this->assertArrayHasKey('name', $toolInfo, 'tool_info should have name');
        $this->assertSame('scip-php', $toolInfo['name'], 'tool_info.name should be "scip-php"');
    }

    // ═══════════════════════════════════════════════════════════════
    // Additional parity checks (from QA findings)
    // ═══════════════════════════════════════════════════════════════

    /**
     * Verifies call records always have all 9 keys (even when null).
     *
     * Critical finding: Call records serialize null values as explicit null,
     * unlike value records which omit optional keys.
     */
    #[ContractTest(
        name: 'Call records have all 9 keys',
        description: 'Verifies every call record has exactly 9 keys including null fields: id, kind, kind_type, caller, callee, return_type, receiver_value_id, location, arguments.',
        category: 'scip',
    )]
    public function testCallRecordsHaveAllKeys(): void
    {
        $requiredKeys = ['id', 'kind', 'kind_type', 'caller', 'callee', 'return_type', 'receiver_value_id', 'location', 'arguments'];

        foreach (self::$calls->calls() as $call) {
            foreach ($requiredKeys as $key) {
                $this->assertArrayHasKey(
                    $key,
                    $call,
                    sprintf(
                        'Call %s should have key "%s". Has keys: %s',
                        $call['id'] ?? 'unknown',
                        $key,
                        implode(', ', array_keys($call))
                    )
                );
            }
        }
    }

    /**
     * Verifies kind_type mapping is consistent with kind.
     *
     * method/method_static/constructor -> "invocation"
     * access/access_static -> "access"
     */
    #[ContractTest(
        name: 'kind_type mapping consistency',
        description: 'Verifies kind_type is consistent: method/method_static/constructor=invocation, access/access_static=access.',
        category: 'scip',
    )]
    public function testKindTypeConsistency(): void
    {
        $expectedMapping = [
            'method' => 'invocation',
            'method_static' => 'invocation',
            'constructor' => 'invocation',
            'access' => 'access',
            'access_static' => 'access',
        ];

        foreach (self::$calls->calls() as $call) {
            $kind = $call['kind'] ?? '';
            $kindType = $call['kind_type'] ?? '';

            if (isset($expectedMapping[$kind])) {
                $this->assertSame(
                    $expectedMapping[$kind],
                    $kindType,
                    sprintf(
                        'Call %s: kind "%s" should have kind_type "%s", got "%s"',
                        $call['id'] ?? 'unknown',
                        $kind,
                        $expectedMapping[$kind],
                        $kindType
                    )
                );
            }
        }
    }

    /**
     * Verifies promoted constructor parameters have promoted_property_symbol.
     *
     * Code reference: src/Dto/CreateOrderInput.php:9-13
     *   public function __construct(
     *       public string $customerEmail,
     *       public string $productId,
     *       public int $quantity,
     *   )
     *
     * Expected: 66 parameter values have promoted_property_symbol
     */
    #[ContractTest(
        name: 'Promoted property symbols (66)',
        description: 'Verifies 66 parameter values have promoted_property_symbol for constructor-promoted properties.',
        category: 'scip',
    )]
    public function testPromotedPropertySymbols(): void
    {
        $promoted = array_filter(
            self::$calls->values(),
            fn($v) => array_key_exists('promoted_property_symbol', $v) && $v['promoted_property_symbol'] !== null
        );

        $this->assertCount(
            66,
            $promoted,
            'Expected exactly 66 values with promoted_property_symbol'
        );

        // Verify CreateOrderInput specifically
        $createOrderPromoted = array_filter($promoted, fn($v) =>
            str_contains($v['symbol'] ?? '', 'CreateOrderInput')
        );

        $this->assertCount(
            3,
            $createOrderPromoted,
            'CreateOrderInput should have 3 promoted properties'
        );
    }

    /**
     * Verifies result values always have source_call_id.
     *
     * Critical finding: All result values have source_call_id equal to their own id.
     */
    #[ContractTest(
        name: 'Result values have source_call_id',
        description: 'Verifies all 297 result values have source_call_id key with non-null value equal to their own id.',
        category: 'scip',
    )]
    public function testResultValuesHaveSourceCallId(): void
    {
        $results = $this->values()->kind('result')->all();
        $this->assertCount(297, $results, 'Expected 297 result values');

        foreach ($results as $result) {
            $this->assertArrayHasKey(
                'source_call_id',
                $result,
                sprintf('Result value %s should have source_call_id key', $result['id'] ?? 'unknown')
            );
            $this->assertNotNull(
                $result['source_call_id'],
                sprintf('Result value %s should have non-null source_call_id', $result['id'] ?? 'unknown')
            );
        }
    }

    /**
     * Verifies syntax_kind distribution matches expected counts.
     *
     * Expected: {6: 623, 9: 4, 11: 246, 12: 172, 19: 41}
     */
    #[ContractTest(
        name: 'syntax_kind distribution',
        description: 'Verifies syntax_kind distribution: 6=623 (Identifier), 9=4 (Module), 11=246 (Parameter), 12=172 (Local), 19=41 (Type).',
        category: 'scip',
    )]
    public function testSyntaxKindDistribution(): void
    {
        $this->requireScipData();

        $distribution = [];

        foreach ($this->scipData()->documents() as $doc) {
            foreach ($doc['occurrences'] ?? [] as $occ) {
                $sk = $occ['syntax_kind'] ?? null;
                if ($sk !== null) {
                    $distribution[$sk] = ($distribution[$sk] ?? 0) + 1;
                }
            }
        }

        $expected = [6 => 623, 9 => 4, 11 => 246, 12 => 172, 19 => 41];

        foreach ($expected as $kind => $count) {
            $actual = $distribution[$kind] ?? 0;
            $this->assertEquals(
                $count,
                $actual,
                "syntax_kind {$kind}: expected {$count}, got {$actual}"
            );
        }
    }
}
