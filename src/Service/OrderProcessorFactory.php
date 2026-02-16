<?php

declare(strict_types=1);

namespace App\Service;

/**
 * Factory for creating order processors.
 *
 * Contract test patterns:
 * - Instantiation of concrete classes
 * - Return type of abstract/parent class
 * - Provides USED BY edges for processor classes
 */
final class OrderProcessorFactory
{
    public function create(string $type): AbstractOrderProcessor
    {
        return match ($type) {
            'standard' => new StandardOrderProcessor(),
            'priority' => new PriorityOrderProcessor(),
            'logging' => new LoggingOrderProcessor(),
            default => throw new \InvalidArgumentException("Unknown processor type: $type"),
        };
    }

    public function createStandard(): StandardOrderProcessor
    {
        return new StandardOrderProcessor();
    }

    public function createPriority(): PriorityOrderProcessor
    {
        return new PriorityOrderProcessor();
    }

    public function createLogging(): LoggingOrderProcessor
    {
        return new LoggingOrderProcessor();
    }
}
