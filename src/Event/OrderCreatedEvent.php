<?php

declare(strict_types=1);

namespace App\Event;

/**
 * Domain event dispatched when an order is created.
 *
 * Contract test patterns:
 * - Event class used with EventDispatcherInterface
 * - Triggers event flow: OrderEventSubscriber listens for this
 * - Cross-flow reference: HTTP flow (OrderController) → dispatches event → event flow
 */
final readonly class OrderCreatedEvent
{
    public function __construct(
        public int $orderId,
        public string $customerEmail,
    ) {
    }
}
