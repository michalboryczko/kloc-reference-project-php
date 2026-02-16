<?php

declare(strict_types=1);

namespace App\Repository;

use App\Entity\Order;

/**
 * Contract test patterns:
 * - Interface extending interface (BaseRepositoryInterface)
 * - Non-scalar parameter and return types
 */
interface OrderRepositoryInterface extends BaseRepositoryInterface
{
    public function findById(int $id): ?Order;

    public function save(Order $order): Order;
}
