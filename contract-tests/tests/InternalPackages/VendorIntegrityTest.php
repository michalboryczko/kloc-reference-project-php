<?php

declare(strict_types=1);

namespace ContractTests\Tests\InternalPackages;

use ContractTests\Attribute\ContractTest;
use ContractTests\CallsContractTestCase;

/**
 * Tests data integrity for vendor code when configured as internal.
 *
 * Verifies that receiver_value_id and argument value_id references in vendor
 * calls point to existing values, and that vendor data doesn't break integrity.
 *
 * Requires: bin/run.sh test --internal
 */
class VendorIntegrityTest extends CallsContractTestCase
{
    /**
     * Vendor calls with receiver_value_id should reference existing values.
     *
     * Code reference: vendor/symfony/messenger/ (method calls on $this, etc.)
     */
    #[ContractTest(
        name: 'Vendor Receiver Value IDs Exist',
        description: 'All receiver_value_id in vendor calls point to existing value entries',
        category: 'internal',
        internal: true,
    )]
    public function testVendorReceiverValueIdsExist(): void
    {
        $vendorCalls = array_filter(
            self::$calls->calls(),
            fn(array $call) => str_contains($call['id'], 'vendor/')
                && !empty($call['receiver_value_id']),
        );

        $this->assertNotEmpty($vendorCalls, 'Should have vendor calls with receivers');

        $invalid = [];
        foreach ($vendorCalls as $call) {
            $receiverId = $call['receiver_value_id'];
            if (!self::$calls->hasValue($receiverId)) {
                $invalid[] = sprintf(
                    'Call %s has receiver_value_id %s that does not exist',
                    $call['id'],
                    $receiverId,
                );
            }
        }

        $this->assertEmpty(
            $invalid,
            sprintf("Found %d invalid receiver_value_id references:\n%s", count($invalid), implode("\n", array_slice($invalid, 0, 5))),
        );
    }

    /**
     * Vendor call arguments with value_id should reference existing values.
     */
    #[ContractTest(
        name: 'Vendor Argument Value IDs Exist',
        description: 'All argument value_id in vendor calls point to existing value entries',
        category: 'internal',
        internal: true,
    )]
    public function testVendorArgumentValueIdsExist(): void
    {
        $vendorCalls = array_filter(
            self::$calls->calls(),
            fn(array $call) => str_contains($call['id'], 'vendor/')
                && !empty($call['arguments']),
        );

        $this->assertNotEmpty($vendorCalls, 'Should have vendor calls with arguments');

        $invalid = [];
        foreach ($vendorCalls as $call) {
            foreach ($call['arguments'] as $arg) {
                $valueId = $arg['value_id'] ?? null;
                if ($valueId !== null && !self::$calls->hasValue($valueId)) {
                    $invalid[] = sprintf(
                        'Call %s argument value_id %s does not exist',
                        $call['id'],
                        $valueId,
                    );
                }
            }
        }

        $this->assertEmpty(
            $invalid,
            sprintf("Found %d invalid argument value_id references:\n%s", count($invalid), implode("\n", array_slice($invalid, 0, 5))),
        );
    }

    /**
     * Vendor values with source_call_id should reference existing calls.
     */
    #[ContractTest(
        name: 'Vendor Source Call IDs Exist',
        description: 'All source_call_id in vendor values point to existing call entries',
        category: 'internal',
        internal: true,
    )]
    public function testVendorSourceCallIdsExist(): void
    {
        $vendorValues = array_filter(
            self::$calls->values(),
            fn(array $value) => str_contains($value['id'], 'vendor/')
                && !empty($value['source_call_id']),
        );

        if (empty($vendorValues)) {
            $this->markTestSkipped('No vendor values with source_call_id found');
        }

        $invalid = [];
        foreach ($vendorValues as $value) {
            $callId = $value['source_call_id'];
            if (!self::$calls->hasCall($callId)) {
                $invalid[] = sprintf(
                    'Value %s has source_call_id %s that does not exist',
                    $value['id'],
                    $callId,
                );
            }
        }

        $this->assertEmpty(
            $invalid,
            sprintf("Found %d invalid source_call_id references:\n%s", count($invalid), implode("\n", array_slice($invalid, 0, 5))),
        );
    }

    /**
     * Project value IDs should have no duplicates when vendor is added.
     */
    #[ContractTest(
        name: 'No Duplicate Project Value IDs',
        description: 'Project (src/) value IDs remain unique when vendor values are added alongside',
        category: 'internal',
        internal: true,
    )]
    public function testNoDuplicateProjectValueIds(): void
    {
        $ids = [];
        $duplicates = [];

        foreach (self::$calls->values() as $value) {
            if (!str_starts_with($value['id'], 'src/')) {
                continue;
            }
            $id = $value['id'];
            if (isset($ids[$id])) {
                $duplicates[] = $id;
            }
            $ids[$id] = true;
        }

        $this->assertEmpty(
            $duplicates,
            sprintf("Found %d duplicate project value IDs:\n%s", count($duplicates), implode("\n", array_slice($duplicates, 0, 5))),
        );
    }

    /**
     * Project call IDs should have no duplicates when vendor is added.
     */
    #[ContractTest(
        name: 'No Duplicate Project Call IDs',
        description: 'Project (src/) call IDs remain unique when vendor calls are added alongside',
        category: 'internal',
        internal: true,
    )]
    public function testNoDuplicateProjectCallIds(): void
    {
        $ids = [];
        $duplicates = [];

        foreach (self::$calls->calls() as $call) {
            if (!str_starts_with($call['id'], 'src/')) {
                continue;
            }
            $id = $call['id'];
            if (isset($ids[$id])) {
                $duplicates[] = $id;
            }
            $ids[$id] = true;
        }

        $this->assertEmpty(
            $duplicates,
            sprintf("Found %d duplicate project call IDs:\n%s", count($duplicates), implode("\n", array_slice($duplicates, 0, 5))),
        );
    }
}
