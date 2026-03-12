<?php

declare(strict_types=1);

namespace ContractTests\Tests\Scip\Parity;

use ContractTests\Attribute\ContractTest;
use ContractTests\CallsContractTestCase;

/**
 * Tests for value record serialization patterns.
 *
 * These tests validate the conditional field presence behavior discovered
 * during QA analysis of the reference output. Values omit optional keys
 * rather than serializing them as null (unlike calls which always have all keys).
 */
class ValueSerializationTest extends CallsContractTestCase
{
    /**
     * Verifies parameter values without promoted properties omit source_call_id
     * and promoted_property_symbol keys entirely.
     *
     * Code reference: src/Component/EmailSender.php:12
     *   public function send(string $to, string $subject, string $body): void
     *
     * Expected: Regular parameter values have keys: id, kind, location, symbol, type
     */
    #[ContractTest(
        name: 'Parameter value key structure',
        description: 'Verifies regular parameter values have exactly: id, kind, location, symbol, type. No source_call_id, no promoted_property_symbol.',
        category: 'scip',
    )]
    public function testParameterValueKeyStructure(): void
    {
        // Find a regular parameter (not promoted)
        $params = $this->values()
            ->kind('parameter')
            ->symbolContains('EmailSender#send().($to)')
            ->all();

        $this->assertNotEmpty($params, 'Should find EmailSender#send().($to) parameter');

        $param = $params[0];
        $this->assertArrayHasKey('id', $param);
        $this->assertArrayHasKey('kind', $param);
        $this->assertArrayHasKey('location', $param);
        $this->assertArrayHasKey('symbol', $param);
        $this->assertArrayHasKey('type', $param);

        // These keys should NOT be present on regular parameters
        $this->assertArrayNotHasKey(
            'source_call_id',
            $param,
            'Regular parameter should not have source_call_id key'
        );
        $this->assertArrayNotHasKey(
            'promoted_property_symbol',
            $param,
            'Non-promoted parameter should not have promoted_property_symbol key'
        );
    }

    /**
     * Verifies promoted parameter values have promoted_property_symbol key.
     *
     * Code reference: src/Dto/CreateOrderInput.php:10
     *   public string $customerEmail,
     *
     * Expected: Promoted parameters have extra promoted_property_symbol key
     */
    #[ContractTest(
        name: 'Promoted parameter has promoted_property_symbol',
        description: 'Verifies constructor-promoted parameters include promoted_property_symbol key pointing to the property symbol.',
        category: 'scip',
    )]
    public function testPromotedParameterHasProperty(): void
    {
        $params = $this->values()
            ->kind('parameter')
            ->symbolContains('CreateOrderInput#__construct().($customerEmail)')
            ->all();

        $this->assertNotEmpty($params, 'Should find CreateOrderInput($customerEmail)');

        $param = $params[0];
        $this->assertArrayHasKey(
            'promoted_property_symbol',
            $param,
            'Promoted parameter should have promoted_property_symbol key'
        );
        $this->assertStringContainsString(
            '$customerEmail.',
            $param['promoted_property_symbol'],
            'promoted_property_symbol should reference the property'
        );
    }

    /**
     * Verifies local values from call results have source_call_id.
     *
     * Code reference: src/Repository/AuditableOrderRepository.php:37
     *   $newOrder = new Order(...)
     *
     * Expected: Local value at assignment has source_call_id pointing to the constructor call
     */
    #[ContractTest(
        name: 'Local from call has source_call_id',
        description: 'Verifies local variables assigned from calls have source_call_id. Example: $newOrder = new Order(...) in AuditableOrderRepository.',
        category: 'scip',
    )]
    public function testLocalFromCallHasSourceCallId(): void
    {
        $locals = $this->values()
            ->kind('local')
            ->symbolContains('AuditableOrderRepository#save().local$newOrder')
            ->all();

        $this->assertNotEmpty($locals, 'Should find $newOrder local value');

        $local = $locals[0];
        $this->assertArrayHasKey(
            'source_call_id',
            $local,
            'Local from call assignment should have source_call_id key'
        );
        $this->assertNotNull(
            $local['source_call_id'],
            'source_call_id should not be null'
        );

        // Verify the source_call_id points to an actual call
        $sourceCall = self::$calls->getCallById($local['source_call_id']);
        $this->assertNotNull(
            $sourceCall,
            sprintf(
                'source_call_id %s should reference an existing call',
                $local['source_call_id']
            )
        );
        $this->assertEquals(
            'constructor',
            $sourceCall['kind'],
            'Source call should be a constructor call'
        );
    }

    /**
     * Verifies local values without call sources omit source_call_id.
     *
     * Code reference: src/Entity/Order.php:27
     *   $parts = explode('@', $this->customerEmail);
     *
     * Note: Some locals with source_call_id come from call results.
     * Locals without sources should omit the key entirely.
     */
    #[ContractTest(
        name: 'Literal value key structure',
        description: 'Verifies literal values have minimal keys: id, kind, location, symbol, type (symbol and type may be null).',
        category: 'scip',
    )]
    public function testLiteralValueKeyStructure(): void
    {
        $literals = $this->values()->kind('literal')->all();
        $this->assertNotEmpty($literals, 'Should find literal values');

        foreach ($literals as $literal) {
            $this->assertArrayHasKey('id', $literal);
            $this->assertArrayHasKey('kind', $literal);
            $this->assertArrayHasKey('location', $literal);

            // Literals should NOT have source_call_id or promoted_property_symbol
            $this->assertArrayNotHasKey(
                'source_call_id',
                $literal,
                sprintf('Literal %s should not have source_call_id', $literal['id'])
            );
            $this->assertArrayNotHasKey(
                'promoted_property_symbol',
                $literal,
                sprintf('Literal %s should not have promoted_property_symbol', $literal['id'])
            );
        }
    }

    /**
     * Verifies constant value key structure.
     *
     * Code reference: src/Ui/Rest/Controller/CustomerController.php:51
     *   Response::HTTP_NOT_FOUND
     *
     * Expected: 4 constant values with symbol pointing to the class constant
     */
    #[ContractTest(
        name: 'Constant value structure',
        description: 'Verifies constant values have symbol pointing to class constant. Expected 4 constant values.',
        category: 'scip',
    )]
    public function testConstantValueStructure(): void
    {
        $constants = $this->values()->kind('constant')->all();
        $this->assertCount(4, $constants, 'Expected 4 constant values');

        foreach ($constants as $constant) {
            $this->assertArrayHasKey('symbol', $constant);
            $this->assertNotNull(
                $constant['symbol'],
                sprintf('Constant %s should have non-null symbol', $constant['id'])
            );
        }
    }

    /**
     * Verifies the 38 local values with source_call_id are properly linked.
     */
    #[ContractTest(
        name: 'Local values with source_call_id (38)',
        description: 'Verifies exactly 38 local values have source_call_id and each references an existing call.',
        category: 'scip',
    )]
    public function testLocalValuesWithSourceCallId(): void
    {
        $localsWithSource = array_filter(
            $this->values()->kind('local')->all(),
            fn($v) => array_key_exists('source_call_id', $v) && $v['source_call_id'] !== null
        );

        $this->assertCount(
            38,
            $localsWithSource,
            'Expected 38 local values with source_call_id'
        );

        // Verify each references an existing call
        foreach ($localsWithSource as $local) {
            $this->assertTrue(
                self::$calls->hasCall($local['source_call_id']),
                sprintf(
                    'Local %s: source_call_id %s should reference existing call',
                    $local['id'],
                    $local['source_call_id']
                )
            );
        }
    }
}
