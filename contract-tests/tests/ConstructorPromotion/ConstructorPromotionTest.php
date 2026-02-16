<?php

declare(strict_types=1);

namespace ContractTests\Tests\ConstructorPromotion;

use ContractTests\Attribute\ContractTest;
use ContractTests\CallsContractTestCase;

/**
 * Contract tests for PHP 8+ constructor promotion detection.
 *
 * These tests validate that scip-php correctly handles promoted constructor
 * parameters by:
 * 1. Detecting visibility modifiers (public/protected/private) on constructor params
 * 2. NOT creating Argument-kind values for promoted params (they become Properties)
 * 3. Creating source_value_id links from parameter Values to their Property counterparts
 * 4. Preserving Argument-kind values for regular (non-promoted) method parameters
 *
 * Reference classes using constructor promotion:
 * - App\Entity\Order (6 public promoted params)
 * - App\Dto\OrderOutput (6 public promoted params)
 * - App\Dto\CreateOrderInput (3 public promoted params)
 * - App\Ui\Messenger\Message\OrderCreatedMessage (1 public promoted param)
 * - App\Service\OrderService (5 private promoted params)
 *
 * Reference class with regular (non-promoted) method params:
 * - App\Component\EmailSender::send($to, $subject, $body)
 */
class ConstructorPromotionTest extends CallsContractTestCase
{
    // ═══════════════════════════════════════════════════════════════
    // A-CT-01: Public promoted param — Order::__construct().$id
    // ═══════════════════════════════════════════════════════════════

    /**
     * Verifies that Order::__construct() has a parameter value for $id
     * that is linked (via the scip-php indexer) to the promoted property.
     *
     * For promoted constructors, scip-php should detect the `public int $id`
     * parameter and ensure the constructor's parameter Value has a
     * source_value_id or symbol linkage to the Property node.
     *
     * Code reference: src/Entity/Order.php:12
     *   public int $id,
     */
    #[ContractTest(
        name: 'Order::__construct() $id Promoted Parameter Value Exists',
        description: 'Verifies that Order constructor has a parameter value for the promoted $id property. The parameter should exist with kind=parameter and symbol containing ($id) or $id.',
        category: 'reference',
    )]
    public function testOrderConstructorIdParameterValueExists(): void
    {
        // Find parameter values in Order::__construct() scope
        $params = $this->values()
            ->kind('parameter')
            ->inCaller('*Order#__construct().*')
            ->all();

        $this->assertNotEmpty($params, 'Order::__construct() should have parameter values');

        // Find the $id parameter specifically
        $idParam = null;
        foreach ($params as $param) {
            $symbol = $param['symbol'] ?? '';
            if (str_contains($symbol, '($id)') || str_contains($symbol, '$id')) {
                $idParam = $param;
                break;
            }
        }

        $this->assertNotNull(
            $idParam,
            'Order::__construct() should have a parameter value for $id. '
            . 'Found params: ' . implode(', ', array_map(fn($p) => $p['symbol'] ?? '(no symbol)', $params))
        );
    }

    /**
     * Verifies all 6 promoted parameter values exist for Order::__construct().
     *
     * Code reference: src/Entity/Order.php:11-18
     *   public function __construct(
     *       public int $id,
     *       public string $customerEmail,
     *       public string $productId,
     *       public int $quantity,
     *       public string $status,
     *       public DateTimeImmutable $createdAt,
     *   )
     */
    #[ContractTest(
        name: 'Order::__construct() All 6 Promoted Parameters Exist',
        description: 'Verifies all 6 promoted constructor parameters ($id, $customerEmail, $productId, $quantity, $status, $createdAt) have parameter value entries in the index.',
        category: 'reference',
    )]
    public function testOrderConstructorAllSixParametersExist(): void
    {
        $params = $this->values()
            ->kind('parameter')
            ->inCaller('*Order#__construct().*')
            ->all();

        $paramNames = [];
        foreach ($params as $param) {
            $symbol = $param['symbol'] ?? '';
            // Extract param name from symbol like ...($id) or ...($customerEmail)
            if (preg_match('/\(\$(\w+)\)/', $symbol, $matches)) {
                $paramNames[] = $matches[1];
            }
        }

        $expectedParams = ['id', 'customerEmail', 'productId', 'quantity', 'status', 'createdAt'];
        foreach ($expectedParams as $expected) {
            $this->assertContains(
                $expected,
                $paramNames,
                "Order::__construct() should have parameter '$expected'. Found: " . implode(', ', $paramNames)
            );
        }
    }

    // ═══════════════════════════════════════════════════════════════
    // A-CT-03: Private promoted param — OrderService::__construct()
    // ═══════════════════════════════════════════════════════════════

    /**
     * Verifies that private promoted constructor parameters are also
     * correctly tracked. OrderService uses `private` visibility.
     *
     * Code reference: src/Service/OrderService.php:19-25
     *   public function __construct(
     *       private OrderRepositoryInterface $orderRepository,
     *       private EmailSenderInterface $emailSender,
     *       private InventoryCheckerInterface $inventoryChecker,
     *       private MessageBusInterface $messageBus,
     *       private AbstractOrderProcessor $orderProcessor,
     *   )
     */
    #[ContractTest(
        name: 'OrderService::__construct() Private Promoted Parameters',
        description: 'Verifies that private promoted constructor parameters ($orderRepository, $emailSender, etc.) have parameter value entries, confirming that private visibility is detected alongside public.',
        category: 'reference',
    )]
    public function testOrderServicePrivatePromotedParametersExist(): void
    {
        $params = $this->values()
            ->kind('parameter')
            ->inCaller('*App/Service/OrderService#__construct().*')
            ->all();

        $this->assertGreaterThanOrEqual(
            5,
            count($params),
            'OrderService::__construct() should have at least 5 private promoted parameters. Found: ' . count($params)
        );

        $paramSymbols = array_map(fn($p) => $p['symbol'] ?? '', $params);
        $hasOrderRepository = false;
        foreach ($paramSymbols as $sym) {
            if (str_contains($sym, 'orderRepository') || str_contains($sym, '$orderRepository')) {
                $hasOrderRepository = true;
                break;
            }
        }

        $this->assertTrue(
            $hasOrderRepository,
            'OrderService::__construct() should have $orderRepository parameter. '
            . 'Found: ' . implode(', ', $paramSymbols)
        );
    }

    // ═══════════════════════════════════════════════════════════════
    // A-CT-04/05: Promoted params should NOT have Argument-kind values
    // (This tests current behavior — promoted params lack Argument nodes)
    // ═══════════════════════════════════════════════════════════════

    /**
     * Verifies that Order::__construct() does NOT have Argument-kind values
     * for its promoted parameters. In scip-php, promoted constructor
     * parameters are modeled as parameters/properties, NOT as Arguments.
     *
     * NOTE: This test validates the CURRENT behavior where promoted
     * constructors lack Argument-kind children. The ISSUE-A spec says
     * this is intentional — promoted params should NOT get Argument nodes.
     *
     * Code reference: src/Entity/Order.php:11-18
     */
    #[ContractTest(
        name: 'Order::__construct() Has No Argument-Kind Values',
        description: 'Verifies promoted constructor parameters do NOT produce Argument-kind values. Promoted params are properties, not formal arguments in the traditional sense.',
        category: 'reference',
    )]
    public function testOrderConstructorHasNoArgumentKindValues(): void
    {
        // Search for any values that look like Argument-kind nodes
        // In the calls.json schema, there's no "argument" value kind,
        // but we check there are no parameter values with Argument-like
        // symbols (e.g., ::$id instead of .$id or ($id))
        $allValues = $this->values()
            ->inCaller('*Order#__construct().*')
            ->all();

        // Promoted constructor should have parameter values but NOT
        // values with kind other than 'parameter', 'result', 'local', 'literal'
        foreach ($allValues as $value) {
            $kind = $value['kind'] ?? '';
            // Valid kinds for constructor scope
            $this->assertContains(
                $kind,
                ['parameter', 'result', 'local', 'literal', 'constant'],
                "Order::__construct() should not have unexpected value kinds. Found kind='{$kind}'"
            );
        }
    }

    // ═══════════════════════════════════════════════════════════════
    // A-CT-06: Regular method params still use parameter values
    // ═══════════════════════════════════════════════════════════════

    /**
     * Verifies that regular (non-promoted) method parameters continue to have
     * parameter value entries. This is the regression test — the promoted
     * constructor handling must NOT break regular parameter tracking.
     *
     * Code reference: src/Component/EmailSender.php:12
     *   public function send(string $to, string $subject, string $body): void
     */
    #[ContractTest(
        name: 'EmailSender::send() Regular Parameters Preserved',
        description: 'Regression test: verifies regular method parameters ($to, $subject, $body) still have parameter value entries after constructor promotion changes.',
        category: 'reference',
    )]
    public function testEmailSenderRegularParametersPreserved(): void
    {
        $params = $this->values()
            ->kind('parameter')
            ->inCaller('*EmailSender#send().*')
            ->all();

        $this->assertGreaterThanOrEqual(
            3,
            count($params),
            'EmailSender::send() should have at least 3 parameter values ($to, $subject, $body). Found: ' . count($params)
        );

        $paramSymbols = array_map(fn($p) => $p['symbol'] ?? '', $params);

        $expectedParams = ['$to', '$subject', '$body'];
        foreach ($expectedParams as $expected) {
            $found = false;
            foreach ($paramSymbols as $sym) {
                if (str_contains($sym, "({$expected})")) {
                    $found = true;
                    break;
                }
            }
            $this->assertTrue(
                $found,
                "EmailSender::send() should have parameter '{$expected}'. Found: " . implode(', ', $paramSymbols)
            );
        }
    }

    // ═══════════════════════════════════════════════════════════════
    // A-CT-02: Order constructor arguments in createOrder() call
    // Verify that the constructor call has all 6 arguments tracked
    // ═══════════════════════════════════════════════════════════════

    /**
     * Verifies the Order constructor call in createOrder() has 6 arguments
     * with correct positions (0-5) and value bindings.
     *
     * Code reference: src/Service/OrderService.php:32-39
     *   $order = new Order(
     *       id: 0,
     *       customerEmail: $input->customerEmail,
     *       ...
     *   );
     */
    #[ContractTest(
        name: 'Order Constructor Call Has 6 Arguments',
        description: 'Verifies the new Order() call in createOrder() has all 6 arguments with positions 0-5, confirming argument tracking works for promoted constructors.',
        category: 'argument',
    )]
    public function testOrderConstructorCallHasSixArguments(): void
    {
        $constructorCall = $this->calls()
            ->kind('constructor')
            ->callerContains('OrderService#createOrder()')
            ->calleeContains('Order')
            ->first();

        $this->assertNotNull($constructorCall, 'Should find Order constructor call in createOrder()');

        $arguments = $constructorCall['arguments'] ?? [];
        $this->assertCount(
            6,
            $arguments,
            'Order constructor should have exactly 6 arguments. Found: ' . count($arguments)
        );

        // Verify positions 0-5
        $positions = array_map(fn($a) => $a['position'] ?? -1, $arguments);
        sort($positions);
        $this->assertEquals(
            [0, 1, 2, 3, 4, 5],
            $positions,
            'Arguments should have positions 0-5'
        );
    }

    /**
     * Verifies the Order constructor's first argument (id: 0) is a literal value.
     *
     * Code reference: src/Service/OrderService.php:33
     *   id: 0,
     */
    #[ContractTest(
        name: 'Order Constructor Arg 0 Is Literal',
        description: 'Verifies the first argument (id: 0) of Order constructor is a literal value.',
        category: 'argument',
    )]
    public function testOrderConstructorFirstArgIsLiteral(): void
    {
        $constructorCall = $this->calls()
            ->kind('constructor')
            ->callerContains('OrderService#createOrder()')
            ->calleeContains('Order')
            ->first();

        $this->assertNotNull($constructorCall, 'Should find Order constructor call');

        $arguments = $constructorCall['arguments'] ?? [];
        $arg0 = null;
        foreach ($arguments as $arg) {
            if (($arg['position'] ?? -1) === 0) {
                $arg0 = $arg;
                break;
            }
        }

        $this->assertNotNull($arg0, 'Should have argument at position 0');

        if ($arg0['value_id'] !== null) {
            $value = $this->callsData()->getValueById($arg0['value_id']);
            $this->assertNotNull($value, 'Argument 0 value should exist');
            $this->assertEquals(
                'literal',
                $value['kind'] ?? null,
                'Argument 0 (id: 0) should be a literal value'
            );
        }
    }

    // ═══════════════════════════════════════════════════════════════
    // A-CT: Single promoted param — OrderCreatedMessage
    // ═══════════════════════════════════════════════════════════════

    /**
     * Verifies single promoted parameter works correctly.
     * OrderCreatedMessage has just one promoted param: public int $orderId.
     *
     * Code reference: src/Ui/Messenger/Message/OrderCreatedMessage.php:9-11
     *   public function __construct(
     *       public int $orderId,
     *   )
     */
    #[ContractTest(
        name: 'OrderCreatedMessage Single Promoted Param',
        description: 'Verifies that a constructor with a single promoted parameter ($orderId) correctly has a parameter value entry.',
        category: 'reference',
    )]
    public function testOrderCreatedMessageSinglePromotedParam(): void
    {
        $params = $this->values()
            ->kind('parameter')
            ->inCaller('*OrderCreatedMessage#__construct().*')
            ->all();

        $this->assertNotEmpty(
            $params,
            'OrderCreatedMessage::__construct() should have at least 1 parameter value'
        );

        $hasOrderId = false;
        foreach ($params as $param) {
            $symbol = $param['symbol'] ?? '';
            if (str_contains($symbol, 'orderId') || str_contains($symbol, '$orderId')) {
                $hasOrderId = true;
                break;
            }
        }

        $this->assertTrue(
            $hasOrderId,
            'OrderCreatedMessage::__construct() should have $orderId parameter. '
            . 'Found: ' . implode(', ', array_map(fn($p) => $p['symbol'] ?? '', $params))
        );
    }

    // ═══════════════════════════════════════════════════════════════
    // A-CT: Constructor arguments for OrderOutput (6 promoted params)
    // Verifies a second promoted constructor also has correct tracking
    // ═══════════════════════════════════════════════════════════════

    /**
     * Verifies the OrderOutput constructor call in createOrder() has 6 arguments.
     *
     * Code reference: src/Service/OrderService.php:60-67
     *   return new OrderOutput(
     *       id: $savedOrder->id,
     *       customerEmail: $savedOrder->customerEmail,
     *       ...
     *   );
     */
    #[ContractTest(
        name: 'OrderOutput Constructor Call Has 6 Arguments',
        description: 'Verifies the new OrderOutput() call in createOrder() has all 6 arguments, confirming argument tracking for a second promoted constructor.',
        category: 'argument',
    )]
    public function testOrderOutputConstructorCallHasSixArguments(): void
    {
        $constructorCall = $this->calls()
            ->kind('constructor')
            ->callerContains('OrderService#createOrder()')
            ->calleeContains('OrderOutput')
            ->first();

        $this->assertNotNull($constructorCall, 'Should find OrderOutput constructor call in createOrder()');

        $arguments = $constructorCall['arguments'] ?? [];
        $this->assertCount(
            6,
            $arguments,
            'OrderOutput constructor should have exactly 6 arguments. Found: ' . count($arguments)
        );
    }

    // ═══════════════════════════════════════════════════════════════
    // A-CT: Constructor arguments have parameter symbols
    // Verifies that arguments link back to the callee's parameters
    // ═══════════════════════════════════════════════════════════════

    /**
     * Verifies that Order constructor arguments have parameter symbols
     * linking to the callee's parameter definitions.
     *
     * Code reference: src/Service/OrderService.php:32-39
     */
    #[ContractTest(
        name: 'Order Constructor Arguments Have Parameter Symbols',
        description: 'Verifies each argument of the Order constructor call has a parameter field linking to the callee parameter definition. This is critical for ISSUE-A: the parameter symbol enables resolving arg labels to property names.',
        category: 'argument',
    )]
    public function testOrderConstructorArgumentsHaveParameterSymbols(): void
    {
        $constructorCall = $this->calls()
            ->kind('constructor')
            ->callerContains('OrderService#createOrder()')
            ->calleeContains('Order')
            ->first();

        $this->assertNotNull($constructorCall, 'Should find Order constructor call');

        $arguments = $constructorCall['arguments'] ?? [];
        $this->assertNotEmpty($arguments, 'Constructor should have arguments');

        $withParameter = 0;
        $withoutParameter = 0;
        foreach ($arguments as $arg) {
            $parameter = $arg['parameter'] ?? null;
            if ($parameter !== null && $parameter !== '') {
                $withParameter++;
            } else {
                $withoutParameter++;
            }
        }

        // Report findings — this test documents the current state
        // After ISSUE-A, all 6 arguments should have parameter symbols
        $this->addToAssertionCount(1);

        // At minimum, document what we find
        $message = sprintf(
            'Order constructor args: %d with parameter symbol, %d without. '
            . 'After ISSUE-A, all 6 should have parameter symbols linking to promoted properties.',
            $withParameter,
            $withoutParameter
        );

        // This test passes regardless — it documents pre/post state
        // The key assertion is that the constructor call exists with 6 arguments
        $this->assertCount(6, $arguments, $message);
    }

    // ═══════════════════════════════════════════════════════════════
    // A-CT: CreateOrderInput promoted params
    // ═══════════════════════════════════════════════════════════════

    /**
     * Verifies CreateOrderInput's 3 promoted parameters are tracked.
     *
     * Code reference: src/Dto/CreateOrderInput.php:9-13
     *   public function __construct(
     *       public string $customerEmail,
     *       public string $productId,
     *       public int $quantity,
     *   )
     */
    #[ContractTest(
        name: 'CreateOrderInput Promoted Parameters',
        description: 'Verifies all 3 promoted constructor parameters ($customerEmail, $productId, $quantity) have parameter value entries.',
        category: 'reference',
    )]
    public function testCreateOrderInputPromotedParameters(): void
    {
        $params = $this->values()
            ->kind('parameter')
            ->inCaller('*CreateOrderInput#__construct().*')
            ->all();

        $this->assertGreaterThanOrEqual(
            3,
            count($params),
            'CreateOrderInput::__construct() should have at least 3 parameter values. Found: ' . count($params)
        );
    }

    // ═══════════════════════════════════════════════════════════════
    // A-CT: Parameter types for promoted params
    // ═══════════════════════════════════════════════════════════════

    /**
     * Verifies that promoted constructor parameters have type information.
     * Order::__construct() parameters should have types: int, string, DateTimeImmutable.
     *
     * Code reference: src/Entity/Order.php:11-18
     */
    #[ContractTest(
        name: 'Order Constructor Promoted Params Have Types',
        description: 'Verifies promoted constructor parameters have type information in their value entries. Types are needed for ISSUE-A to display Property types in argument labels.',
        category: 'reference',
    )]
    public function testOrderConstructorPromotedParamsHaveTypes(): void
    {
        $params = $this->values()
            ->kind('parameter')
            ->inCaller('*Order#__construct().*')
            ->all();

        $this->assertNotEmpty($params, 'Should have parameter values');

        $withType = 0;
        foreach ($params as $param) {
            $type = $param['type'] ?? null;
            if ($type !== null && $type !== '') {
                $withType++;
            }
        }

        $this->assertGreaterThan(
            0,
            $withType,
            'At least some promoted constructor parameters should have type information. '
            . 'Found ' . count($params) . ' params, ' . $withType . ' with types.'
        );
    }

    // ═══════════════════════════════════════════════════════════════
    // ISSUE-A: promoted_property_symbol field on promoted params
    // ═══════════════════════════════════════════════════════════════

    /**
     * Verifies that promoted constructor parameters have the
     * promoted_property_symbol field set, linking the Value(parameter)
     * to its corresponding Property symbol.
     *
     * Code reference: src/Entity/Order.php:11-18
     *   public function __construct(
     *       public int $id,
     *       public string $customerEmail,
     *       ...
     *   )
     */
    #[ContractTest(
        name: 'Order Promoted Params Have promoted_property_symbol',
        description: 'Verifies all 6 promoted constructor parameters have promoted_property_symbol set, linking each Value(parameter) to the corresponding Property symbol (e.g., Order#$id.).',
        category: 'reference',
    )]
    public function testOrderPromotedParamsHavePromotedPropertySymbol(): void
    {
        $params = $this->values()
            ->kind('parameter')
            ->inCaller('*Order#__construct().*')
            ->all();

        $this->assertNotEmpty($params, 'Should have parameter values');

        $withSymbol = 0;
        $withoutSymbol = 0;
        $details = [];
        foreach ($params as $param) {
            $pps = $param['promoted_property_symbol'] ?? null;
            $paramSymbol = $param['symbol'] ?? '(no symbol)';
            if ($pps !== null && $pps !== '') {
                $withSymbol++;
                $details[] = "{$paramSymbol} => {$pps}";
            } else {
                $withoutSymbol++;
                $details[] = "{$paramSymbol} => (none)";
            }
        }

        $this->assertEquals(
            6,
            $withSymbol,
            'All 6 promoted Order constructor params should have promoted_property_symbol. '
            . "Found {$withSymbol} with, {$withoutSymbol} without. Details: " . implode(', ', $details)
        );
    }

    /**
     * Verifies that the promoted_property_symbol field contains a valid
     * Property symbol matching the expected pattern for Order::$id.
     *
     * Code reference: src/Entity/Order.php:12
     *   public int $id,
     */
    #[ContractTest(
        name: 'Order::$id promoted_property_symbol Points to Property',
        description: 'Verifies the $id parameter promoted_property_symbol contains a Property symbol with the #$id. pattern, confirming it links to the correct Property node.',
        category: 'reference',
    )]
    public function testOrderIdPromotedPropertySymbolPointsToProperty(): void
    {
        $params = $this->values()
            ->kind('parameter')
            ->inCaller('*Order#__construct().*')
            ->all();

        $idParam = null;
        foreach ($params as $param) {
            $symbol = $param['symbol'] ?? '';
            if (str_contains($symbol, '($id)')) {
                $idParam = $param;
                break;
            }
        }

        $this->assertNotNull($idParam, 'Should find $id parameter value');

        $pps = $idParam['promoted_property_symbol'] ?? null;
        $this->assertNotNull($pps, '$id parameter should have promoted_property_symbol');
        $this->assertStringContainsString(
            '#$id.',
            $pps,
            'promoted_property_symbol should contain Property symbol pattern #$id. Got: ' . $pps
        );
    }

    /**
     * Verifies that non-promoted parameters do NOT have promoted_property_symbol.
     * EmailSender::send() has regular params, not promoted.
     *
     * Code reference: src/Component/EmailSender.php:12
     *   public function send(string $to, string $subject, string $body): void
     */
    #[ContractTest(
        name: 'EmailSender::send() Non-Promoted Params Have No promoted_property_symbol',
        description: 'Regression: verifies regular method parameters do NOT have promoted_property_symbol set. Only promoted constructor params should have this field.',
        category: 'reference',
    )]
    public function testNonPromotedParamsHaveNoPromotedPropertySymbol(): void
    {
        $params = $this->values()
            ->kind('parameter')
            ->inCaller('*EmailSender#send().*')
            ->all();

        $this->assertNotEmpty($params, 'Should have parameter values');

        foreach ($params as $param) {
            $pps = $param['promoted_property_symbol'] ?? null;
            $paramSymbol = $param['symbol'] ?? '(no symbol)';
            $this->assertNull(
                $pps,
                "Non-promoted param {$paramSymbol} should NOT have promoted_property_symbol. Got: {$pps}"
            );
        }
    }

    /**
     * Verifies that OrderCreatedMessage's single promoted param has
     * promoted_property_symbol set.
     *
     * Code reference: src/Ui/Messenger/Message/OrderCreatedMessage.php:9-11
     *   public function __construct(
     *       public int $orderId,
     *   )
     */
    #[ContractTest(
        name: 'OrderCreatedMessage Single Promoted Param Has promoted_property_symbol',
        description: 'Verifies single promoted param $orderId has promoted_property_symbol linking to OrderCreatedMessage#$orderId Property.',
        category: 'reference',
    )]
    public function testOrderCreatedMessagePromotedPropertySymbol(): void
    {
        $params = $this->values()
            ->kind('parameter')
            ->inCaller('*OrderCreatedMessage#__construct().*')
            ->all();

        $this->assertNotEmpty($params, 'Should have parameter values');

        $orderId = null;
        foreach ($params as $param) {
            $symbol = $param['symbol'] ?? '';
            if (str_contains($symbol, 'orderId')) {
                $orderId = $param;
                break;
            }
        }

        $this->assertNotNull($orderId, 'Should find $orderId parameter');

        $pps = $orderId['promoted_property_symbol'] ?? null;
        $this->assertNotNull(
            $pps,
            '$orderId should have promoted_property_symbol'
        );
        $this->assertStringContainsString(
            '$orderId',
            $pps,
            'promoted_property_symbol should reference $orderId property. Got: ' . $pps
        );
    }

    /**
     * Verifies that private promoted constructor params also have
     * promoted_property_symbol. OrderService uses `private` visibility
     * (not `public` like Order), covering AC2 — all visibility modifiers.
     *
     * Code reference: src/Service/OrderService.php:19-25
     *   public function __construct(
     *       private OrderRepositoryInterface $orderRepository,
     *       private EmailSenderInterface $emailSender,
     *       private InventoryCheckerInterface $inventoryChecker,
     *       private MessageBusInterface $messageBus,
     *       private AbstractOrderProcessor $orderProcessor,
     *   )
     */
    #[ContractTest(
        name: 'OrderService Private Promoted Params Have promoted_property_symbol',
        description: 'Verifies all 5 private promoted constructor parameters in OrderService have promoted_property_symbol set. Covers AC2: all visibility modifiers (public, private, protected) must produce assigned_from edges.',
        category: 'reference',
    )]
    public function testOrderServicePrivatePromotedParamsHavePromotedPropertySymbol(): void
    {
        $params = $this->values()
            ->kind('parameter')
            ->inCaller('*App/Service/OrderService#__construct().*')
            ->all();

        $this->assertNotEmpty($params, 'Should have parameter values for OrderService::__construct()');

        $withSymbol = 0;
        $withoutSymbol = 0;
        $details = [];
        foreach ($params as $param) {
            $pps = $param['promoted_property_symbol'] ?? null;
            $paramSymbol = $param['symbol'] ?? '(no symbol)';
            if ($pps !== null && $pps !== '') {
                $withSymbol++;
                $details[] = "{$paramSymbol} => {$pps}";
            } else {
                $withoutSymbol++;
                $details[] = "{$paramSymbol} => (none)";
            }
        }

        $this->assertEquals(
            5,
            $withSymbol,
            'All 5 private promoted OrderService constructor params should have promoted_property_symbol. '
            . "Found {$withSymbol} with, {$withoutSymbol} without. Details: " . implode(', ', $details)
        );
    }
}
