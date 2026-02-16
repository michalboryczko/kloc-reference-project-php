<?php

declare(strict_types=1);

namespace ContractTests\Tests\InternalPackages;

use ContractTests\Attribute\ContractTest;
use ContractTests\CallsContractTestCase;

/**
 * Tests that calls within and to vendor code are tracked when configured as internal.
 *
 * When symfony/messenger is internal, calls inside its source files appear
 * in the calls array, and project-to-vendor calls resolve to vendor symbols.
 *
 * Requires: bin/run.sh test --internal
 */
class VendorCallsTest extends CallsContractTestCase
{
    /**
     * Calls within vendor files should appear when package is internal.
     *
     * Code reference: vendor/symfony/messenger/ (method calls inside vendor code)
     */
    #[ContractTest(
        name: 'Vendor File Calls Exist',
        description: 'Calls with vendor/ in their id exist, confirming vendor code method calls are tracked',
        category: 'internal',
        internal: true,
    )]
    public function testVendorFileCallsExist(): void
    {
        $vendorCalls = array_filter(
            self::$calls->calls(),
            fn(array $call) => str_contains($call['id'], 'vendor/'),
        );

        $this->assertNotEmpty(
            $vendorCalls,
            'Internal package should have calls tracked within vendor files',
        );
        $this->assertGreaterThan(
            100,
            count($vendorCalls),
            'symfony/messenger should contribute substantial number of vendor calls',
        );
    }

    /**
     * Project-to-vendor calls should resolve to vendor callee symbols.
     *
     * OrderService::createOrder() calls $this->messageBus->dispatch() which is
     * MessageBusInterface::dispatch() — a symfony/messenger symbol.
     *
     * Code reference: src/Service/OrderService.php:58
     *   $this->messageBus->dispatch(new OrderCreatedMessage($savedOrder->id));
     */
    #[ContractTest(
        name: 'Dispatch Call Resolves to Vendor Symbol',
        description: 'The dispatch() call in OrderService resolves to MessageBusInterface#dispatch() vendor callee symbol',
        category: 'internal',
        internal: true,
    )]
    public function testDispatchCallResolvesToVendorSymbol(): void
    {
        $dispatchCalls = array_filter(
            self::$calls->calls(),
            fn(array $call) => str_contains($call['callee'] ?? '', 'MessageBusInterface#dispatch'),
        );

        $this->assertNotEmpty(
            $dispatchCalls,
            'Should find dispatch() call with MessageBusInterface#dispatch callee symbol',
        );

        $call = array_values($dispatchCalls)[0];
        $this->assertSame('method', $call['kind']);
        $this->assertSame('invocation', $call['kind_type']);
        $this->assertStringContainsString(
            'OrderService#createOrder()',
            $call['caller'],
            'Caller should be OrderService::createOrder()',
        );
    }

    /**
     * Vendor calls should have proper structure (kind, kind_type, callee).
     */
    #[ContractTest(
        name: 'Vendor Calls Have Valid Structure',
        description: 'Calls within vendor files have required fields: kind, kind_type, caller, callee',
        category: 'internal',
        internal: true,
    )]
    public function testVendorCallsHaveValidStructure(): void
    {
        $vendorCalls = array_filter(
            self::$calls->calls(),
            fn(array $call) => str_contains($call['id'], 'vendor/'),
        );

        $this->assertNotEmpty($vendorCalls);

        $checked = 0;
        foreach (array_slice(array_values($vendorCalls), 0, 20) as $call) {
            $this->assertArrayHasKey('kind', $call, "Vendor call {$call['id']} missing kind");
            $this->assertArrayHasKey('kind_type', $call, "Vendor call {$call['id']} missing kind_type");
            $this->assertArrayHasKey('caller', $call, "Vendor call {$call['id']} missing caller");
            $this->assertArrayHasKey('callee', $call, "Vendor call {$call['id']} missing callee");
            $this->assertNotEmpty($call['caller'], "Vendor call {$call['id']} has empty caller");
            $this->assertNotEmpty($call['callee'], "Vendor call {$call['id']} has empty callee");
            $checked++;
        }

        $this->assertGreaterThan(0, $checked);
    }

    /**
     * Total call count should exceed baseline when internal package is added.
     */
    #[ContractTest(
        name: 'Call Count Exceeds Baseline',
        description: 'With symfony/messenger as internal, total call count exceeds the baseline project-only count',
        category: 'internal',
        internal: true,
    )]
    public function testCallCountExceedsBaseline(): void
    {
        $totalCalls = self::$calls->callCount();
        $projectCalls = count(array_filter(
            self::$calls->calls(),
            fn(array $call) => str_starts_with($call['id'], 'src/'),
        ));

        $this->assertGreaterThan(
            $projectCalls,
            $totalCalls,
            'Total calls should exceed project-only calls when internal package is configured',
        );
    }
}
