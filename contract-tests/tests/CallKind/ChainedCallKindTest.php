<?php

declare(strict_types=1);

namespace ContractTests\Tests\CallKind;

use ContractTests\Attribute\ContractTest;
use ContractTests\CallsContractTestCase;

/**
 * Tests for call_kind accuracy in chained expressions.
 *
 * Validates that scip-php correctly distinguishes method calls from property
 * accesses in chained expressions like $this->property->method().
 *
 * Related issues:
 * - Issue 3: getName() misclassified as property_access
 * - Issue 6: Defensive fallback for incorrect call_kind
 */
class ChainedCallKindTest extends CallsContractTestCase
{
    // =================================================================
    // Issue 3: Chained method calls must have kind=method
    // =================================================================

    /**
     * Verifies that getName() in $this->orderProcessor->getName() has kind=method.
     *
     * Code reference: src/Service/OrderService.php:43
     *   $processorName = $this->orderProcessor->getName();
     *
     * Issue 3: The chained method call getName() was misclassified as
     * property_access (kind=access) instead of method call (kind=method).
     * The indexer must distinguish ->property (access) from ->method() (method).
     */
    #[ContractTest(
        name: 'Chained method call getName() has kind=method',
        description: 'Verifies $this->orderProcessor->getName() call has kind=method, not kind=access. Issue 3: chained method calls must not be misclassified as property access.',
        category: 'callkind',
    )]
    public function testChainedMethodCallGetNameHasKindMethod(): void
    {
        // Find the getName() call in OrderService::createOrder()
        $getNameCalls = $this->calls()
            ->kind('method')
            ->callerContains('OrderService#createOrder()')
            ->calleeContains('getName')
            ->all();

        $this->assertNotEmpty(
            $getNameCalls,
            'Should find getName() as a method call (kind=method) in OrderService::createOrder(). ' .
            'If empty, getName() may be misclassified with wrong kind (e.g., access instead of method).'
        );

        $call = $getNameCalls[0];
        $this->assertSame('method', $call['kind'], 'getName() must have kind=method');
        $this->assertSame('invocation', $call['kind_type'], 'getName() must have kind_type=invocation');
        $this->assertStringContainsString(
            'AbstractOrderProcessor#getName()',
            $call['callee'] ?? '',
            'Callee should reference AbstractOrderProcessor#getName()'
        );
    }

    /**
     * Verifies that $this->orderProcessor (the property access step) has kind=access.
     *
     * Code reference: src/Service/OrderService.php:43
     *   $processorName = $this->orderProcessor->getName();
     *
     * The property access step in the chain must be kind=access, not kind=method.
     */
    #[ContractTest(
        name: 'Property access $this->orderProcessor has kind=access',
        description: 'Verifies the property access step in $this->orderProcessor->getName() has kind=access, confirming the indexer correctly distinguishes property access from method call in chains.',
        category: 'callkind',
    )]
    public function testPropertyAccessOrderProcessorHasKindAccess(): void
    {
        // Find the $this->orderProcessor access at line 43
        $accessCalls = $this->calls()
            ->kind('access')
            ->callerContains('OrderService#createOrder()')
            ->calleeContains('$orderProcessor')
            ->atLine(43)
            ->all();

        $this->assertNotEmpty(
            $accessCalls,
            'Should find $this->orderProcessor property access at line 43'
        );

        $call = $accessCalls[0];
        $this->assertSame('access', $call['kind'], 'Property access must have kind=access');
        $this->assertSame('access', $call['kind_type'], 'Property access must have kind_type=access');
    }

    /**
     * Verifies that process() in $this->orderProcessor->process($order) has kind=method.
     *
     * Code reference: src/Service/OrderService.php:42
     *   $processedOrder = $this->orderProcessor->process($order);
     *
     * Same pattern as getName() -- validates consistency of chained method call classification.
     */
    #[ContractTest(
        name: 'Chained method call process() has kind=method',
        description: 'Verifies $this->orderProcessor->process($order) call has kind=method. Validates that chained method calls consistently get kind=method across different methods.',
        category: 'callkind',
    )]
    public function testChainedMethodCallProcessHasKindMethod(): void
    {
        $processCalls = $this->calls()
            ->kind('method')
            ->callerContains('OrderService#createOrder()')
            ->calleeContains('process')
            ->all();

        // Filter to only AbstractOrderProcessor#process (exclude orderProcessor property access)
        $processCalls = array_filter($processCalls, function (array $c): bool {
            return str_contains($c['callee'] ?? '', 'AbstractOrderProcessor#process()');
        });
        $processCalls = array_values($processCalls);

        $this->assertNotEmpty(
            $processCalls,
            'Should find process() as a method call (kind=method) in OrderService::createOrder()'
        );

        $call = $processCalls[0];
        $this->assertSame('method', $call['kind'], 'process() must have kind=method');
        $this->assertSame('invocation', $call['kind_type'], 'process() must have kind_type=invocation');
    }

    // =================================================================
    // Issue 2: Static property access must not inherit constructor kind
    // =================================================================

    /**
     * Verifies self::$nextId++ at line 30 has kind=access_static, not constructor.
     *
     * Code reference: src/Repository/OrderRepository.php:30
     *   id: self::$nextId++,
     *
     * Issue 2: The static property access was incorrectly classified with
     * the constructor's kind because find_call_for_usage() matched the wrong
     * Call node at the same line.
     */
    #[ContractTest(
        name: 'Static property self::$nextId has kind=access_static',
        description: 'Verifies self::$nextId++ in OrderRepository::save() has kind=access_static at line 30. Issue 2: static property access must not inherit the constructor kind from new Order() at line 29.',
        category: 'callkind',
    )]
    public function testStaticPropertyNextIdHasKindAccessStatic(): void
    {
        $staticAccessCalls = $this->calls()
            ->kind('access_static')
            ->callerContains('OrderRepository#save()')
            ->calleeContains('$nextId')
            ->all();

        $this->assertNotEmpty(
            $staticAccessCalls,
            'Should find self::$nextId as access_static in OrderRepository::save(). ' .
            'If empty, the static property access may be missing or misclassified.'
        );

        $call = $staticAccessCalls[0];
        $this->assertSame('access_static', $call['kind'], 'self::$nextId must have kind=access_static');
        $this->assertSame('access', $call['kind_type'], 'Static access must have kind_type=access');
        $this->assertStringContainsString(
            'OrderRepository#$nextId',
            $call['callee'] ?? '',
            'Callee should reference OrderRepository#$nextId'
        );
    }

    /**
     * Verifies new Order(...) at line 29 has kind=constructor, distinct from
     * the static property access on the next line.
     *
     * Code reference: src/Repository/OrderRepository.php:29
     *   $newOrder = new Order(
     */
    #[ContractTest(
        name: 'Constructor new Order() at line 29 has kind=constructor',
        description: 'Verifies new Order() constructor call in save() has kind=constructor at line 29, distinct from the self::$nextId access_static at line 30.',
        category: 'callkind',
    )]
    public function testConstructorNewOrderHasKindConstructor(): void
    {
        $constructorCalls = $this->calls()
            ->kind('constructor')
            ->callerContains('OrderRepository#save()')
            ->calleeContains('Order#__construct')
            ->all();

        $this->assertNotEmpty(
            $constructorCalls,
            'Should find new Order() constructor in OrderRepository::save()'
        );

        $call = $constructorCalls[0];
        $this->assertSame('constructor', $call['kind']);
        $this->assertSame('invocation', $call['kind_type']);

        // Constructor should be at line 29, not line 30
        $line = $call['location']['line'] ?? 0;
        $this->assertSame(
            29,
            $line,
            'Constructor new Order() should be at line 29'
        );
    }

    // =================================================================
    // Consistency: No method calls misclassified as access
    // =================================================================

    /**
     * Verifies there are no calls with kind=access whose callee contains
     * a method signature pattern (ending with "()"), which would indicate
     * a method call misclassified as property access.
     */
    #[ContractTest(
        name: 'No method calls misclassified as access',
        description: 'Verifies no calls have kind=access with a callee that looks like a method (containing "()"). This guards against Issue 3 regression where method calls in chains get kind=access.',
        category: 'callkind',
    )]
    public function testNoMethodCallsMisclassifiedAsAccess(): void
    {
        $accessCalls = $this->calls()
            ->kind('access')
            ->all();

        $misclassified = [];
        foreach ($accessCalls as $call) {
            $callee = $call['callee'] ?? '';
            // Check if callee looks like a method (has "()" before the final ".")
            // Methods: "Class#method()." Properties: "Class#$property."
            if (preg_match('/#[^$][^.]*\(\)\.$/', $callee)) {
                $misclassified[] = sprintf(
                    'Call %s has kind=access but callee %s looks like a method',
                    $call['id'] ?? 'unknown',
                    $callee
                );
            }
        }

        $this->assertEmpty(
            $misclassified,
            sprintf(
                "Found %d calls with kind=access but method-like callee (Issue 3 regression):\n%s",
                count($misclassified),
                implode("\n", array_slice($misclassified, 0, 10))
            )
        );
    }
}
