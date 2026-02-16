<?php

declare(strict_types=1);

namespace App\Component;

use App\Entity\Order;

/**
 * Interface for order processors.
 *
 * Contract test patterns:
 * - Interface with non-scalar types in signatures
 * - Multiple methods
 */
interface OrderProcessorInterface
{
    public function process(Order $order): Order;

    public function getName(): string;
}
