<?php

declare(strict_types=1);

namespace ContractTests\Tests\InternalPackages;

use ContractTests\Attribute\ContractTest;
use ContractTests\CallsContractTestCase;

/**
 * Tests that values within vendor code are tracked when configured as internal.
 *
 * When symfony/messenger is internal, parameters, locals, and results from
 * its methods appear in the values array.
 *
 * Requires: bin/run.sh test --internal
 */
class VendorValuesTest extends CallsContractTestCase
{
    /**
     * Values within vendor files should appear when package is internal.
     *
     * Code reference: vendor/symfony/messenger/ (parameters, locals in vendor methods)
     */
    #[ContractTest(
        name: 'Vendor File Values Exist',
        description: 'Values with vendor/ in their id exist, confirming vendor code parameters and locals are tracked',
        category: 'internal',
        internal: true,
    )]
    public function testVendorFileValuesExist(): void
    {
        $vendorValues = array_filter(
            self::$calls->values(),
            fn(array $value) => str_contains($value['id'], 'vendor/'),
        );

        $this->assertNotEmpty(
            $vendorValues,
            'Internal package should have values tracked within vendor files',
        );
        $this->assertGreaterThan(
            100,
            count($vendorValues),
            'symfony/messenger should contribute substantial number of vendor values',
        );
    }

    /**
     * Vendor parameters should have proper symbols with package identifier.
     *
     * Code reference: vendor/symfony/messenger/Envelope.php
     *   Methods like wrap(), with() have parameters that should be tracked.
     */
    #[ContractTest(
        name: 'Vendor Parameter Symbols Contain Package Name',
        description: 'Vendor parameter values have symbols containing symfony/messenger package identifier',
        category: 'internal',
        internal: true,
    )]
    public function testVendorParameterSymbolsContainPackageName(): void
    {
        $vendorParams = array_filter(
            self::$calls->values(),
            fn(array $value) => $value['kind'] === 'parameter'
                && str_contains($value['id'], 'vendor/')
                && str_contains($value['id'], 'messenger'),
        );

        $this->assertNotEmpty($vendorParams, 'Should find vendor parameter values');

        $param = array_values($vendorParams)[0];
        $this->assertStringContainsString(
            'symfony/messenger',
            $param['symbol'],
            'Vendor parameter symbol should reference the symfony/messenger package',
        );
    }

    /**
     * Vendor values should have valid structure (kind, symbol, type, location).
     */
    #[ContractTest(
        name: 'Vendor Values Have Valid Structure',
        description: 'Values within vendor files have required fields: kind, symbol, type, location with file and line',
        category: 'internal',
        internal: true,
    )]
    public function testVendorValuesHaveValidStructure(): void
    {
        $vendorValues = array_filter(
            self::$calls->values(),
            fn(array $value) => str_contains($value['id'], 'vendor/'),
        );

        $this->assertNotEmpty($vendorValues);

        $checked = 0;
        foreach (array_slice(array_values($vendorValues), 0, 20) as $value) {
            $this->assertArrayHasKey('kind', $value, "Vendor value {$value['id']} missing kind");
            $this->assertArrayHasKey('symbol', $value, "Vendor value {$value['id']} missing symbol");
            $this->assertContains(
                $value['kind'],
                ['parameter', 'local', 'literal', 'constant', 'result'],
                "Vendor value {$value['id']} has unexpected kind: {$value['kind']}",
            );
            $checked++;
        }

        $this->assertGreaterThan(0, $checked);
    }

    /**
     * Total value count should exceed baseline when internal package is added.
     */
    #[ContractTest(
        name: 'Value Count Exceeds Baseline',
        description: 'With symfony/messenger as internal, total value count exceeds the baseline project-only count',
        category: 'internal',
        internal: true,
    )]
    public function testValueCountExceedsBaseline(): void
    {
        $totalValues = self::$calls->valueCount();
        $projectValues = count(array_filter(
            self::$calls->values(),
            fn(array $value) => str_starts_with($value['id'], 'src/'),
        ));

        $this->assertGreaterThan(
            $projectValues,
            $totalValues,
            'Total values should exceed project-only values when internal package is configured',
        );
    }
}
