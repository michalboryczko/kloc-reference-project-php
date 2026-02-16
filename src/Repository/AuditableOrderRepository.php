<?php

declare(strict_types=1);

namespace App\Repository;

use App\Component\AuditableInterface;
use App\Entity\Order;
use DateTimeImmutable;

/**
 * Order repository with audit logging.
 *
 * Contract test patterns:
 * - Class implementing multiple interfaces (OrderRepositoryInterface + AuditableInterface)
 * - Override methods from two different interfaces
 */
final class AuditableOrderRepository implements OrderRepositoryInterface, AuditableInterface
{
    /** @var array<int, Order> */
    private array $orders = [];

    private int $nextId = 1;

    /** @var array<string> */
    private array $auditLog = [];

    public function findById(int $id): ?Order
    {
        $this->auditLog[] = 'findById:' . $id;
        return $this->orders[$id] ?? null;
    }

    public function save(Order $order): Order
    {
        if ($order->id === 0) {
            $newOrder = new Order(
                id: $this->nextId++,
                customerEmail: $order->customerEmail,
                productId: $order->productId,
                quantity: $order->quantity,
                status: $order->status,
                createdAt: $order->createdAt,
            );
            $this->orders[$newOrder->id] = $newOrder;
            $this->auditLog[] = 'save:created:' . $newOrder->id;

            return $newOrder;
        }

        $this->orders[$order->id] = $order;
        $this->auditLog[] = 'save:updated:' . $order->id;

        return $order;
    }

    /**
     * @return array<int, Order>
     */
    public function findAll(): array
    {
        $this->auditLog[] = 'findAll';
        return $this->orders;
    }

    /**
     * @return array<string>
     */
    public function getAuditLog(): array
    {
        return $this->auditLog;
    }
}
