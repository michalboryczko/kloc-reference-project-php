<?php

declare(strict_types=1);

namespace ContractTests\Tests\Chain;

use ContractTests\Attribute\ContractTest;
use ContractTests\CallsContractTestCase;

/**
 * Tests for chain linkage in chained expressions.
 *
 * Validates that multi-step chains like $this->property->method() maintain
 * proper value linkage: access produces result value, method call uses that
 * result value as its receiver.
 *
 * Related issues:
 * - Issue 3: Chain linkage for $this->orderProcessor->getName()
 * - Issue 4: Chain linkage for $this->emailSender->send()
 */
class ChainedExpressionTest extends CallsContractTestCase
{
    // =================================================================
    // Chain: $this->orderProcessor->getName()
    // =================================================================

    /**
     * Verifies the full chain $this->orderProcessor->getName() is properly linked.
     *
     * Code reference: src/Service/OrderService.php:43
     *   $processorName = $this->orderProcessor->getName();
     *
     * Expected chain:
     *   access($orderProcessor) -> result value -> method(getName) -> result value
     *
     * The getName() method call's receiver_value_id must point to the result
     * value produced by the $orderProcessor property access.
     */
    #[ContractTest(
        name: 'Chain: $this->orderProcessor->getName()',
        description: 'Verifies the chained expression $this->orderProcessor->getName() has proper linkage: property access produces result value, method call uses it as receiver. Issue 3: validates chain integrity for the misclassified pattern.',
        category: 'chain',
    )]
    public function testChainOrderProcessorGetName(): void
    {
        // Step 1: Find getName() method call
        $getNameCall = $this->calls()
            ->kind('method')
            ->callerContains('OrderService#createOrder()')
            ->calleeContains('getName')
            ->first();

        $this->assertNotNull($getNameCall, 'Should find getName() method call');

        // Step 2: getName() must have a receiver_value_id
        $receiverId = $getNameCall['receiver_value_id'] ?? null;
        $this->assertNotNull(
            $receiverId,
            'getName() call must have receiver_value_id (the result of $this->orderProcessor access)'
        );

        // Step 3: The receiver value must be a result value from the orderProcessor access
        $receiverValue = self::$calls->getValueById($receiverId);
        $this->assertNotNull($receiverValue, 'Receiver value must exist');
        $this->assertSame(
            'result',
            $receiverValue['kind'] ?? '',
            'getName() receiver should be a result value (from orderProcessor property access)'
        );

        // Step 4: The result value's source_call_id should point to the orderProcessor access
        $sourceCallId = $receiverValue['source_call_id'] ?? '';
        $this->assertNotEmpty($sourceCallId, 'Result value should have source_call_id');

        $sourceCall = self::$calls->getCallById($sourceCallId);
        $this->assertNotNull($sourceCall, 'Source call should exist');
        $this->assertSame(
            'access',
            $sourceCall['kind'] ?? '',
            'Source call should be a property access (kind=access)'
        );
        $this->assertStringContainsString(
            '$orderProcessor',
            $sourceCall['callee'] ?? '',
            'Source call should access $orderProcessor property'
        );
    }

    // =================================================================
    // Chain: $this->emailSender->send()
    // =================================================================

    /**
     * Verifies the chain $this->emailSender->send(...) is properly linked.
     *
     * Code reference: src/Service/OrderService.php:47
     *   $this->emailSender->send(
     *       to: $savedOrder->customerEmail,
     *       ...
     *   );
     *
     * Expected chain:
     *   access($emailSender) -> result value -> method(send) -> result value
     */
    #[ContractTest(
        name: 'Chain: $this->emailSender->send()',
        description: 'Verifies the chained expression $this->emailSender->send() has proper linkage: property access produces result, method call uses it as receiver. Issue 4: validates chain for the named-arguments pattern.',
        category: 'chain',
    )]
    public function testChainEmailSenderSend(): void
    {
        // Step 1: Find send() method call
        $sendCall = $this->calls()
            ->kind('method')
            ->callerContains('OrderService#createOrder()')
            ->calleeContains('send')
            ->first();

        $this->assertNotNull($sendCall, 'Should find send() method call');

        // Step 2: send() must have a receiver_value_id
        $receiverId = $sendCall['receiver_value_id'] ?? null;
        $this->assertNotNull(
            $receiverId,
            'send() call must have receiver_value_id (the result of $this->emailSender access)'
        );

        // Step 3: The receiver value must be a result value from the emailSender access
        $receiverValue = self::$calls->getValueById($receiverId);
        $this->assertNotNull($receiverValue, 'Receiver value must exist');
        $this->assertSame(
            'result',
            $receiverValue['kind'] ?? '',
            'send() receiver should be a result value (from emailSender property access)'
        );

        // Step 4: The result value's source_call_id should point to the emailSender access
        $sourceCallId = $receiverValue['source_call_id'] ?? '';
        $this->assertNotEmpty($sourceCallId, 'Result value should have source_call_id');

        $sourceCall = self::$calls->getCallById($sourceCallId);
        $this->assertNotNull($sourceCall, 'Source call should exist');
        $this->assertSame(
            'access',
            $sourceCall['kind'] ?? '',
            'Source call should be a property access (kind=access)'
        );
        $this->assertStringContainsString(
            '$emailSender',
            $sourceCall['callee'] ?? '',
            'Source call should access $emailSender property'
        );
    }

    // =================================================================
    // Chain: $this->orderRepository->save()
    // =================================================================

    /**
     * Verifies the chain $this->orderRepository->save() has proper linkage
     * and the result value is stored in $savedOrder local.
     *
     * Code reference: src/Service/OrderService.php:45
     *   $savedOrder = $this->orderRepository->save($processedOrder);
     */
    #[ContractTest(
        name: 'Chain: $this->orderRepository->save() to $savedOrder',
        description: 'Verifies the chained expression $this->orderRepository->save() produces a result value that flows to $savedOrder local variable via source_call_id.',
        category: 'chain',
    )]
    public function testChainOrderRepositorySaveToLocal(): void
    {
        // Step 1: Find save() method call
        $saveCall = $this->calls()
            ->kind('method')
            ->callerContains('OrderService#createOrder()')
            ->calleeContains('save')
            ->first();

        $this->assertNotNull($saveCall, 'Should find save() method call');

        // Step 2: Find $savedOrder local variable
        $savedOrderLocal = $this->inMethod('App\Service\OrderService', 'createOrder')
            ->values()
            ->kind('local')
            ->symbolContains('local$savedOrder')
            ->first();

        $this->assertNotNull($savedOrderLocal, 'Should find $savedOrder local variable');

        // Step 3: $savedOrder should have source_call_id pointing to save() call
        $this->assertSame(
            $saveCall['id'],
            $savedOrderLocal['source_call_id'] ?? '',
            '$savedOrder local should have source_call_id pointing to save() call'
        );
    }
}
