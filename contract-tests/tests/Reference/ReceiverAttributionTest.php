<?php

declare(strict_types=1);

namespace ContractTests\Tests\Reference;

use ContractTests\Attribute\ContractTest;
use ContractTests\CallsContractTestCase;

/**
 * Tests for correct receiver attribution in property accesses.
 *
 * Validates that property accesses inside method call arguments (including
 * named arguments) correctly reference their actual receiver, not the
 * enclosing method call's receiver.
 *
 * Related issues:
 * - Issue 4: Named arguments misattributed to enclosing call receiver
 * - Issue 2: Constructor arguments inherit wrong reference type
 */
class ReceiverAttributionTest extends CallsContractTestCase
{
    // =================================================================
    // Issue 4: Property access in named arguments
    // =================================================================

    /**
     * Verifies $savedOrder->customerEmail inside send() named arg has correct receiver.
     *
     * Code reference: src/Service/OrderService.php:48
     *   to: $savedOrder->customerEmail,
     *
     * Issue 4: The property access was misattributed to $this->emailSender
     * (the send() method's receiver) instead of $savedOrder (the actual receiver).
     */
    #[ContractTest(
        name: '$savedOrder->customerEmail receiver in send() args',
        description: 'Verifies $savedOrder->customerEmail at line 48 (inside send() named argument) has receiver_value_id pointing to $savedOrder local, NOT to the emailSender property access result. Issue 4: named arguments must not inherit enclosing call receiver.',
        category: 'reference',
    )]
    public function testSavedOrderCustomerEmailReceiverInSendArgs(): void
    {
        // Find the $savedOrder->customerEmail access at line 48
        $customerEmailAccess = $this->calls()
            ->kind('access')
            ->callerContains('OrderService#createOrder()')
            ->calleeContains('$customerEmail')
            ->atLine(48)
            ->first();

        $this->assertNotNull(
            $customerEmailAccess,
            'Should find $savedOrder->customerEmail property access at line 48'
        );

        // It must have a receiver_value_id
        $receiverId = $customerEmailAccess['receiver_value_id'] ?? null;
        $this->assertNotNull(
            $receiverId,
            '$savedOrder->customerEmail access must have receiver_value_id'
        );

        // The receiver must be the $savedOrder local variable, not the emailSender result
        $receiverValue = self::$calls->getValueById($receiverId);
        $this->assertNotNull($receiverValue, 'Receiver value must exist');

        // Verify it's a local variable (not a result from emailSender access)
        $this->assertSame(
            'local',
            $receiverValue['kind'] ?? '',
            'Receiver should be $savedOrder local variable, not a result value from emailSender access'
        );
        $this->assertStringContainsString(
            'local$savedOrder',
            $receiverValue['symbol'] ?? '',
            'Receiver symbol should contain local$savedOrder'
        );
    }

    /**
     * Verifies $savedOrder->id inside send() named arg has correct receiver.
     *
     * Code reference: src/Service/OrderService.php:49
     *   subject: 'Order Confirmation #' . $savedOrder->id,
     */
    #[ContractTest(
        name: '$savedOrder->id receiver in send() args',
        description: 'Verifies $savedOrder->id at line 49 (inside send() named argument) has receiver_value_id pointing to $savedOrder local. Same pattern as Issue 4 customerEmail test.',
        category: 'reference',
    )]
    public function testSavedOrderIdReceiverInSendArgs(): void
    {
        // Find the $savedOrder->id access at line 49
        $idAccess = $this->calls()
            ->kind('access')
            ->callerContains('OrderService#createOrder()')
            ->calleeContains('$id')
            ->atLine(49)
            ->first();

        $this->assertNotNull(
            $idAccess,
            'Should find $savedOrder->id property access at line 49'
        );

        $receiverId = $idAccess['receiver_value_id'] ?? null;
        $this->assertNotNull(
            $receiverId,
            '$savedOrder->id access must have receiver_value_id'
        );

        $receiverValue = self::$calls->getValueById($receiverId);
        $this->assertNotNull($receiverValue, 'Receiver value must exist');

        $this->assertSame(
            'local',
            $receiverValue['kind'] ?? '',
            'Receiver should be $savedOrder local variable'
        );
        $this->assertStringContainsString(
            'local$savedOrder',
            $receiverValue['symbol'] ?? '',
            'Receiver symbol should contain local$savedOrder'
        );
    }

    // =================================================================
    // Receiver consistency: multiple accesses share same receiver
    // =================================================================

    /**
     * Verifies all property accesses on $savedOrder in createOrder() share
     * the same receiver_value_id.
     *
     * Code reference: src/Service/OrderService.php:48, 49, 52-54, 61-66
     *   Multiple accesses: $savedOrder->customerEmail, $savedOrder->id, etc.
     */
    #[ContractTest(
        name: 'All $savedOrder accesses share same receiver',
        description: 'Verifies all property accesses on $savedOrder in OrderService::createOrder() share the same receiver_value_id, confirming consistent variable tracking across multiple access sites.',
        category: 'reference',
    )]
    public function testAllSavedOrderAccessesShareReceiver(): void
    {
        // Find all property accesses in createOrder() that have a receiver
        $allAccesses = $this->calls()
            ->kind('access')
            ->callerContains('OrderService#createOrder()')
            ->hasReceiver()
            ->all();

        // Filter to accesses whose receiver is a local$savedOrder value
        $savedOrderAccesses = [];
        foreach ($allAccesses as $access) {
            $receiverId = $access['receiver_value_id'] ?? '';
            $receiverValue = self::$calls->getValueById($receiverId);
            if ($receiverValue !== null &&
                str_contains($receiverValue['symbol'] ?? '', 'local$savedOrder')) {
                $savedOrderAccesses[] = $access;
            }
        }

        $this->assertGreaterThanOrEqual(
            2,
            count($savedOrderAccesses),
            'Should find multiple property accesses on $savedOrder'
        );

        // Collect unique receiver IDs
        $receiverIds = array_unique(array_map(
            fn(array $a) => $a['receiver_value_id'] ?? '',
            $savedOrderAccesses
        ));

        $this->assertCount(
            1,
            $receiverIds,
            sprintf(
                'All $savedOrder accesses should share the same receiver_value_id, found %d different: %s',
                count($receiverIds),
                implode(', ', $receiverIds)
            )
        );
    }

    /**
     * Verifies all property accesses on $order in OrderRepository::save()
     * share the same receiver_value_id pointing to the $order parameter.
     *
     * Code reference: src/Repository/OrderRepository.php:31-35
     *   $order->customerEmail, $order->productId, $order->quantity,
     *   $order->status, $order->createdAt
     */
    #[ContractTest(
        name: 'All $order accesses in save() share same receiver',
        description: 'Verifies all property accesses on $order in OrderRepository::save() share the same receiver_value_id pointing to the $order parameter value.',
        category: 'reference',
    )]
    public function testAllOrderAccessesInSaveShareReceiver(): void
    {
        // Find all property accesses in save() with receivers
        $allAccesses = $this->inMethod('App\Repository\OrderRepository', 'save')
            ->calls()
            ->kind('access')
            ->hasReceiver()
            ->all();

        // Filter to only accesses on the $order parameter (lines 28, 31-35, 42)
        // Exclude accesses on $newOrder local (line 37)
        $orderParamAccesses = [];
        foreach ($allAccesses as $access) {
            $receiverId = $access['receiver_value_id'] ?? '';
            $receiverValue = self::$calls->getValueById($receiverId);
            if ($receiverValue !== null &&
                ($receiverValue['kind'] ?? '') === 'parameter' &&
                str_contains($receiverValue['symbol'] ?? '', '($order)')) {
                $orderParamAccesses[] = $access;
            }
        }

        $this->assertGreaterThanOrEqual(
            5,
            count($orderParamAccesses),
            'Should find at least 5 property accesses on $order parameter in save() ' .
            '(customerEmail, productId, quantity, status, createdAt)'
        );

        // Verify they all share the same receiver_value_id
        $receiverIds = array_unique(array_map(
            fn(array $a) => $a['receiver_value_id'] ?? '',
            $orderParamAccesses
        ));

        $this->assertCount(
            1,
            $receiverIds,
            sprintf(
                'All $order accesses in save() should share the same receiver_value_id, found %d: %s',
                count($receiverIds),
                implode(', ', $receiverIds)
            )
        );
    }

    // =================================================================
    // Issue 2: Property access inside constructor arguments
    // =================================================================

    /**
     * Verifies $order->customerEmail at line 31 inside new Order() constructor
     * args has its own separate call entry with correct receiver.
     *
     * Code reference: src/Repository/OrderRepository.php:31
     *   customerEmail: $order->customerEmail,
     *
     * Issue 2: Property accesses inside constructor argument lists must get
     * their own call records, not inherit the constructor's metadata.
     */
    #[ContractTest(
        name: '$order->customerEmail in constructor args has own call entry',
        description: 'Verifies $order->customerEmail at line 31 inside new Order() constructor arguments has its own call entry with kind=access and receiver pointing to $order parameter. Issue 2: constructor arg property accesses must not inherit constructor metadata.',
        category: 'reference',
    )]
    public function testOrderCustomerEmailInConstructorArgsHasOwnCall(): void
    {
        // Find the $order->customerEmail access at line 31 in save()
        $customerEmailAccess = $this->calls()
            ->kind('access')
            ->callerContains('OrderRepository#save()')
            ->calleeContains('$customerEmail')
            ->atLine(31)
            ->first();

        $this->assertNotNull(
            $customerEmailAccess,
            'Should find $order->customerEmail as a separate access call at line 31'
        );

        // It must be kind=access (not constructor)
        $this->assertSame('access', $customerEmailAccess['kind']);

        // Verify it has a receiver pointing to $order parameter
        $receiverId = $customerEmailAccess['receiver_value_id'] ?? null;
        $this->assertNotNull($receiverId, 'Access should have receiver_value_id');

        $receiverValue = self::$calls->getValueById($receiverId);
        $this->assertNotNull($receiverValue, 'Receiver value should exist');
        $this->assertSame('parameter', $receiverValue['kind'] ?? '');
        $this->assertStringContainsString(
            '($order)',
            $receiverValue['symbol'] ?? '',
            'Receiver should be the $order parameter'
        );
    }
}
