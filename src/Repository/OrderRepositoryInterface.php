<?php

declare(strict_types=1);

namespace App\Repository;

use App\Entity\Order;

interface OrderRepositoryInterface
{
    public function findById(int $id): ?Order;

    public function save(Order $order): Order;
}
