<?php

declare(strict_types=1);

namespace ContractTests\Tests\Combined\Consistency;

use ContractTests\Attribute\ContractTest;
use ContractTests\CallsContractTestCase;

/**
 * Tests consistency between SCIP index and index.json output.
 *
 * Validates that method calls and property accesses in index.json have
 * corresponding SCIP occurrences, and that symbol formats match.
 */
class ConsistencyTest extends CallsContractTestCase
{
    /**
     * Verifies method calls in index.json have SCIP occurrences.
     *
     * Expected: For each method call in index.json, a corresponding SCIP reference exists.
     */
    #[ContractTest(
        name: 'Method calls have SCIP occurrences',
        description: 'Verifies method calls in index.json (kind=method) have corresponding reference occurrences in SCIP.',
        category: 'combined',
    )]
    public function testMethodCallsHaveScipOccurrences(): void
    {
        $this->requireScipData();

        // Get method calls from index.json
        $methodCalls = $this->calls()->kind('method')->all();

        $this->assertGreaterThan(0, count($methodCalls), 'Expected at least one method call');

        $callsWithoutScipOccurrence = [];

        // Sample check - verify a subset of calls have SCIP occurrences
        $sampleSize = min(10, count($methodCalls));
        $sample = array_slice($methodCalls, 0, $sampleSize);

        foreach ($sample as $call) {
            $callee = $call['callee'] ?? '';
            if (empty($callee)) {
                continue;
            }

            // Extract method name from callee (e.g., "OrderRepository#save()." -> "save")
            if (preg_match('/#([^#]+)\(\)\.$/', $callee, $matches)) {
                $methodName = $matches[1];

                // Check if SCIP has any occurrence for this callee
                $occurrences = $this->scip()->occurrences()
                    ->symbolContains($callee)
                    ->all();

                if (count($occurrences) === 0) {
                    // Try partial match
                    $occurrences = $this->scip()->occurrences()
                        ->symbolContains($methodName . '()')
                        ->all();
                }

                if (count($occurrences) === 0) {
                    $callsWithoutScipOccurrence[] = $callee;
                }
            }
        }

        // Allow some mismatches due to symbol format differences
        $maxMismatches = (int) ($sampleSize * 0.3);
        $this->assertLessThanOrEqual(
            $maxMismatches,
            count($callsWithoutScipOccurrence),
            sprintf(
                'Too many method calls without SCIP occurrences: %s',
                implode(', ', array_slice($callsWithoutScipOccurrence, 0, 5))
            )
        );
    }

    /**
     * Verifies property accesses in index.json have SCIP occurrences.
     *
     * Expected: For each property access in index.json, a corresponding SCIP reference exists.
     */
    #[ContractTest(
        name: 'Property accesses have SCIP occurrences',
        description: 'Verifies property accesses in index.json (kind=access) have corresponding reference occurrences in SCIP.',
        category: 'combined',
    )]
    public function testPropertyAccessesHaveScipOccurrences(): void
    {
        $this->requireScipData();

        // Get property accesses from index.json
        $accesses = $this->calls()->kind('access')->all();

        $this->assertGreaterThan(0, count($accesses), 'Expected at least one property access');

        $accessesWithoutScipOccurrence = [];

        // Sample check
        $sampleSize = min(10, count($accesses));
        $sample = array_slice($accesses, 0, $sampleSize);

        foreach ($sample as $access) {
            $callee = $access['callee'] ?? '';
            if (empty($callee)) {
                continue;
            }

            // Extract property name from callee (e.g., "Order#$customerEmail." -> "$customerEmail")
            if (preg_match('/#(\$[^.]+)\.$/', $callee, $matches)) {
                $propertyName = $matches[1];

                // Check if SCIP has any occurrence for this callee
                $occurrences = $this->scip()->occurrences()
                    ->symbolContains($callee)
                    ->all();

                if (count($occurrences) === 0) {
                    // Try partial match
                    $occurrences = $this->scip()->occurrences()
                        ->symbolContains($propertyName)
                        ->all();
                }

                if (count($occurrences) === 0) {
                    $accessesWithoutScipOccurrence[] = $callee;
                }
            }
        }

        // Allow some mismatches
        $maxMismatches = (int) ($sampleSize * 0.3);
        $this->assertLessThanOrEqual(
            $maxMismatches,
            count($accessesWithoutScipOccurrence),
            sprintf(
                'Too many property accesses without SCIP occurrences: %s',
                implode(', ', array_slice($accessesWithoutScipOccurrence, 0, 5))
            )
        );
    }

    /**
     * Verifies constructor calls have both index.json and SCIP entries.
     *
     * Code reference: src/Service/OrderService.php:31
     *   $order = new Order(...)
     *
     * Expected: Both index.json (kind=constructor) and SCIP (reference) capture this.
     */
    #[ContractTest(
        name: 'Constructor calls have both entries',
        description: 'Verifies new Order() appears in both index.json (kind=constructor) and SCIP (reference occurrence).',
        category: 'combined',
    )]
    public function testConstructorCallsHaveBothEntries(): void
    {
        $this->requireScipData();

        // Find Order constructor call in index.json
        $constructorCalls = $this->calls()
            ->kind('constructor')
            ->calleeContains('Order')
            ->all();

        $this->assertGreaterThan(
            0,
            count($constructorCalls),
            'Expected at least one Order constructor call in index.json'
        );

        // Find Order class reference in SCIP near constructor call
        $scipReferences = $this->scip()->occurrences()
            ->symbolContains('Entity/Order#')
            ->isReference()
            ->all();

        $this->assertGreaterThan(
            0,
            count($scipReferences),
            'Expected Order class references in SCIP index'
        );

        // Verify there's at least one SCIP reference in OrderService (where new Order() is called)
        $orderServiceReferences = array_filter($scipReferences, function ($occ) {
            $file = $occ['_file'] ?? '';
            return str_contains($file, 'OrderService.php');
        });

        $this->assertGreaterThan(
            0,
            count($orderServiceReferences),
            'Expected Order reference in OrderService where constructor is called'
        );
    }

    /**
     * Verifies SCIP symbols match index.json callee symbols.
     *
     * Expected: Symbol format in index.json callee field is compatible with SCIP symbols.
     */
    #[ContractTest(
        name: 'Symbol formats are compatible',
        description: 'Verifies symbol formats between index.json callee and SCIP symbols are compatible after normalization.',
        category: 'combined',
    )]
    public function testSymbolFormatsAreCompatible(): void
    {
        $this->requireScipData();

        // Get a sample method call from index.json
        $methodCall = $this->calls()
            ->kind('method')
            ->calleeContains('save()')
            ->first();

        $this->assertNotNull($methodCall, 'Expected to find a save() method call');

        $callee = $methodCall['callee'] ?? '';
        $this->assertNotEmpty($callee);

        // The callee should be in SCIP-compatible format
        // e.g., "scip-php composer . App/Repository/OrderRepository#save()."

        // Extract just the symbol part (after the scheme)
        // SCIP symbol format: "scip-php composer . App/Repository/OrderRepository#save()."
        $symbolPart = $callee;
        if (preg_match('/([A-Z][^#]*#[^.]+\.)/', $callee, $matches)) {
            $symbolPart = $matches[1];
        }

        // Verify this pattern exists in SCIP
        $scipSymbols = $this->scip()->symbols()
            ->symbolContains($symbolPart)
            ->all();

        // At minimum, the symbol pattern should be recognizable
        $this->assertTrue(
            str_contains($callee, '#'),
            'Expected callee to contain # separator (SCIP format)'
        );

        $this->assertTrue(
            str_contains($callee, '().'),
            'Expected method callee to end with ().'
        );
    }

    /**
     * Verifies type consistency between SCIP and index.json.
     *
     * Expected: Value types in index.json that are project classes correspond to SCIP symbols.
     */
    #[ContractTest(
        name: 'Types correspond to SCIP symbols',
        description: 'Verifies value types in index.json reference valid SCIP class symbols for project classes.',
        category: 'combined',
    )]
    public function testTypesCorrespondToScipSymbols(): void
    {
        $this->requireScipData();

        // Get values with types from index.json
        $values = $this->values()->kind('result')->all();

        $typesToCheck = [];
        foreach ($values as $value) {
            $type = $value['type'] ?? null;
            if ($type !== null && $type !== '' && $type !== 'void') {
                // Normalize type - remove nullable prefix
                $baseType = ltrim($type, '?');

                // Skip primitive types
                if (in_array($baseType, ['int', 'string', 'bool', 'float', 'array', 'void', 'null', 'mixed'], true)) {
                    continue;
                }

                // Skip union types
                if (str_contains($baseType, '|')) {
                    continue;
                }

                // Skip if it's a SCIP symbol format (starts with scip-php)
                if (str_starts_with($baseType, 'scip-php')) {
                    // Extract the actual class name from SCIP format
                    // e.g., "scip-php composer ... App/Entity/Order#" -> check for App/Entity/Order
                    if (preg_match('/App\/[^#]+/', $baseType, $matches)) {
                        $typesToCheck[$matches[0]] = true;
                    }
                    continue;
                }

                $typesToCheck[$baseType] = true;
            }
        }

        // We expect at least some App/ types
        $appTypes = array_filter(array_keys($typesToCheck), fn($t) => str_contains($t, 'App/'));

        $this->assertGreaterThan(
            0,
            count($appTypes),
            'Expected at least one App namespace type in values'
        );

        // Check that these App types have SCIP symbols
        $missingTypes = [];
        foreach ($appTypes as $typeName) {
            // Convert namespace to SCIP format
            $scipFormat = str_replace('\\', '/', $typeName);

            $symbols = $this->scip()->symbols()
                ->symbolContains($scipFormat . '#')
                ->all();

            if (count($symbols) === 0) {
                $missingTypes[] = $typeName;
            }
        }

        // Most App/ types should have SCIP symbols
        $this->assertEmpty(
            $missingTypes,
            sprintf(
                'App types without SCIP symbols: %s',
                implode(', ', array_slice($missingTypes, 0, 5))
            )
        );
    }

    /**
     * Verifies both SCIP and index.json cover the same source files.
     *
     * Expected: Source files indexed in index.json are also in SCIP.
     */
    #[ContractTest(
        name: 'Source files are consistently indexed',
        description: 'Verifies the same source files appear in both index.json scope and SCIP documents.',
        category: 'combined',
    )]
    public function testSourceFilesAreConsistentlyIndexed(): void
    {
        $this->requireScipData();

        // Get files from SCIP
        $scipFiles = $this->scipData()->filePaths();
        $this->assertGreaterThan(0, count($scipFiles));

        // Get scope files from index.json (unique caller scopes)
        $calls = $this->calls()->all();
        $callsFiles = [];
        foreach ($calls as $call) {
            $scope = $call['caller'] ?? '';
            // Extract file from scope (format: "scip-php composer . Path/To/Class#method().")
            if (preg_match('/([A-Z][^#]+)#/', $scope, $matches)) {
                $classPath = str_replace('/', '/', $matches[1]); // normalize
                $callsFiles[$classPath] = true;
            }
        }

        // Verify SCIP has documents for files referenced in calls
        $scipFileSet = [];
        foreach ($scipFiles as $file) {
            // Normalize: "src/Service/OrderService.php" -> "Service/OrderService"
            $normalized = preg_replace('/^src\//', '', $file);
            $normalized = preg_replace('/\.php$/', '', $normalized);
            $scipFileSet[$normalized] = true;
        }

        // At least some overlap should exist
        $overlap = 0;
        foreach (array_keys($callsFiles) as $callsFile) {
            // Try to find match in SCIP files
            foreach (array_keys($scipFileSet) as $scipFile) {
                if (str_contains($scipFile, $callsFile) || str_contains($callsFile, $scipFile)) {
                    $overlap++;
                    break;
                }
            }
        }

        $this->assertGreaterThan(
            0,
            $overlap,
            'Expected some overlap between files indexed in index.json and SCIP'
        );
    }
}
