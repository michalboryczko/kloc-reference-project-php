<?php

declare(strict_types=1);

namespace ContractTests\Tests\Integrity;

use ContractTests\Attribute\ContractTest;
use ContractTests\CallsContractTestCase;

/**
 * Tests for location accuracy of calls in calls.json.
 *
 * Validates that call locations point to the actual source code position
 * of the operation, not to an enclosing expression's position.
 *
 * Related issues:
 * - Issue 2: Uses edge location for self::$nextId++ points to line 29 (constructor)
 *   instead of line 30 (actual static property access)
 * - Issue 4: Property accesses in method arguments get wrong location
 */
class LocationAccuracyTest extends CallsContractTestCase
{
    // =================================================================
    // Issue 2: Static property access location
    // =================================================================

    /**
     * Verifies self::$nextId++ at line 30 has location.line=30 (not 29).
     *
     * Code reference: src/Repository/OrderRepository.php:29-30
     *   $newOrder = new Order(          // line 29
     *       id: self::$nextId++,        // line 30
     *
     * Issue 2: The static property access location was incorrectly set to
     * line 29 (the constructor line) instead of line 30 (the actual line).
     */
    #[ContractTest(
        name: 'self::$nextId location is line 30 (not 29)',
        description: 'Verifies the access_static call for self::$nextId++ has location.line=30, not line 29 (the constructor line). Issue 2: static property access in constructor args must have accurate location.',
        category: 'integrity',
    )]
    public function testStaticPropertyNextIdLocationIsLine30(): void
    {
        $staticAccessCalls = $this->calls()
            ->kind('access_static')
            ->callerContains('OrderRepository#save()')
            ->calleeContains('$nextId')
            ->all();

        $this->assertNotEmpty(
            $staticAccessCalls,
            'Should find self::$nextId access_static call'
        );

        $call = $staticAccessCalls[0];
        $location = $call['location'] ?? [];

        $this->assertSame(
            30,
            $location['line'] ?? 0,
            'self::$nextId++ location should be line 30, not line 29 (Issue 2: ' .
            'static property access must not inherit constructor expression line)'
        );

        $this->assertStringContainsString(
            'OrderRepository.php',
            $location['file'] ?? '',
            'Location file should be OrderRepository.php'
        );
    }

    /**
     * Verifies constructor new Order() and self::$nextId++ are on different lines.
     *
     * Code reference: src/Repository/OrderRepository.php:29-30
     *
     * This ensures the two adjacent operations (constructor and static property
     * access) have distinct, accurate locations.
     */
    #[ContractTest(
        name: 'Constructor and static access have distinct locations',
        description: 'Verifies new Order() constructor at line 29 and self::$nextId++ at line 30 have different location lines. Issue 2: adjacent operations must not share locations.',
        category: 'integrity',
    )]
    public function testConstructorAndStaticAccessHaveDistinctLocations(): void
    {
        // Find constructor
        $constructorCall = $this->calls()
            ->kind('constructor')
            ->callerContains('OrderRepository#save()')
            ->calleeContains('Order#__construct')
            ->first();

        $this->assertNotNull($constructorCall, 'Should find Order constructor');
        $constructorLine = $constructorCall['location']['line'] ?? 0;

        // Find static access
        $staticCall = $this->calls()
            ->kind('access_static')
            ->callerContains('OrderRepository#save()')
            ->calleeContains('$nextId')
            ->first();

        $this->assertNotNull($staticCall, 'Should find self::$nextId access');
        $staticLine = $staticCall['location']['line'] ?? 0;

        $this->assertNotSame(
            $constructorLine,
            $staticLine,
            sprintf(
                'Constructor (line %d) and static property access (line %d) should be on different lines',
                $constructorLine,
                $staticLine
            )
        );
    }

    // =================================================================
    // Property access locations inside constructor arguments
    // =================================================================

    /**
     * Verifies property accesses inside new Order() constructor arguments
     * have accurate locations matching their actual source lines.
     *
     * Code reference: src/Repository/OrderRepository.php:31-35
     *   customerEmail: $order->customerEmail,  // line 31
     *   productId: $order->productId,          // line 32
     *   quantity: $order->quantity,             // line 33
     *   status: $order->status,                // line 34
     *   createdAt: $order->createdAt,          // line 35
     */
    #[ContractTest(
        name: 'Property accesses in constructor args have correct line numbers',
        description: 'Verifies $order->customerEmail (line 31), $order->productId (line 32), etc. inside new Order() constructor arguments have accurate location.line values matching their actual source lines.',
        category: 'integrity',
    )]
    public function testPropertyAccessesInConstructorArgsHaveCorrectLines(): void
    {
        $expectedAccesses = [
            ['callee_pattern' => '$customerEmail', 'expected_line' => 31],
            ['callee_pattern' => '$productId', 'expected_line' => 32],
            ['callee_pattern' => '$quantity', 'expected_line' => 33],
            ['callee_pattern' => '$status', 'expected_line' => 34],
            ['callee_pattern' => '$createdAt', 'expected_line' => 35],
        ];

        $errors = [];
        foreach ($expectedAccesses as $expected) {
            $access = $this->calls()
                ->kind('access')
                ->callerContains('OrderRepository#save()')
                ->calleeContains($expected['callee_pattern'])
                ->first();

            if ($access === null) {
                $errors[] = sprintf(
                    'No access call found for %s in save()',
                    $expected['callee_pattern']
                );
                continue;
            }

            $actualLine = $access['location']['line'] ?? 0;
            if ($actualLine !== $expected['expected_line']) {
                $errors[] = sprintf(
                    '%s: expected line %d, got line %d',
                    $expected['callee_pattern'],
                    $expected['expected_line'],
                    $actualLine
                );
            }
        }

        $this->assertEmpty(
            $errors,
            sprintf(
                "Property access location errors in constructor arguments:\n%s",
                implode("\n", $errors)
            )
        );
    }

    // =================================================================
    // Property access locations inside method call arguments
    // =================================================================

    /**
     * Verifies property accesses inside send() named arguments have accurate
     * location lines, not inheriting the enclosing send() call's location.
     *
     * Code reference: src/Service/OrderService.php:47-54
     *   $this->emailSender->send(
     *       to: $savedOrder->customerEmail,          // line 48
     *       subject: 'Order Confirmation #' . $savedOrder->id,  // line 49
     *       ...
     *   );
     */
    #[ContractTest(
        name: 'Property accesses in send() args have correct line numbers',
        description: 'Verifies $savedOrder->customerEmail (line 48) and $savedOrder->id (line 49) inside send() named arguments have accurate location.line values. Issue 4: property accesses in method args must not inherit enclosing call location.',
        category: 'integrity',
    )]
    public function testPropertyAccessesInSendArgsHaveCorrectLines(): void
    {
        // $savedOrder->customerEmail should be at line 48
        $customerEmailAccess = $this->calls()
            ->kind('access')
            ->callerContains('OrderService#createOrder()')
            ->calleeContains('$customerEmail')
            ->atLine(48)
            ->first();

        $this->assertNotNull(
            $customerEmailAccess,
            'Should find $savedOrder->customerEmail access at line 48'
        );

        // $savedOrder->id should be at line 49
        $idAccess = $this->calls()
            ->kind('access')
            ->callerContains('OrderService#createOrder()')
            ->calleeContains('$id')
            ->atLine(49)
            ->first();

        $this->assertNotNull(
            $idAccess,
            'Should find $savedOrder->id access at line 49'
        );

        // Neither should be at line 47 (the send() call line)
        $sendCallLine = 47;

        $customerEmailLine = $customerEmailAccess['location']['line'] ?? 0;
        $this->assertNotSame(
            $sendCallLine,
            $customerEmailLine,
            '$savedOrder->customerEmail should not be at the send() call line (47)'
        );

        $idLine = $idAccess['location']['line'] ?? 0;
        $this->assertNotSame(
            $sendCallLine,
            $idLine,
            '$savedOrder->id should not be at the send() call line (47)'
        );
    }

    // =================================================================
    // General location accuracy
    // =================================================================

    /**
     * Verifies that no two calls at the same line have conflicting callee symbols,
     * which would indicate location conflation between adjacent operations.
     *
     * This is a broader check for Issue 2: when multiple operations occur at
     * nearby lines (like a constructor and its arguments), each must have its
     * own distinct location.
     */
    #[ContractTest(
        name: 'No duplicate call IDs with different callees',
        description: 'Verifies that each call has a unique ID (file:line:col). Duplicate IDs with different callees would indicate location conflation between operations.',
        category: 'integrity',
    )]
    public function testNoDuplicateCallIdsWithDifferentCallees(): void
    {
        $callsByIdMap = [];
        $conflicts = [];

        foreach (self::$calls->calls() as $call) {
            $id = $call['id'] ?? '';
            $callee = $call['callee'] ?? '';

            if (isset($callsByIdMap[$id])) {
                if ($callsByIdMap[$id] !== $callee) {
                    $conflicts[] = sprintf(
                        'Call ID %s has conflicting callees: %s vs %s',
                        $id,
                        $callsByIdMap[$id],
                        $callee
                    );
                }
            } else {
                $callsByIdMap[$id] = $callee;
            }
        }

        $this->assertEmpty(
            $conflicts,
            sprintf(
                "Found %d calls with duplicate IDs but different callees:\n%s",
                count($conflicts),
                implode("\n", array_slice($conflicts, 0, 10))
            )
        );
    }
}
