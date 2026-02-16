<?php

declare(strict_types=1);

namespace App\Repository;

use App\Entity\Order;

/**
 * Versioned order repository with 3-level interface chain.
 *
 * Contract test patterns:
 * - Chain of interfaces: VersionedOrderRepositoryInterface
 *     extends OrderRepositoryInterface
 *       extends BaseRepositoryInterface
 * - Override methods from all 3 levels
 */
final class VersionedOrderRepository implements VersionedOrderRepositoryInterface
{
    /** @var array<int, array{order: Order, version: int}> */
    private array $orders = [];

    private int $nextId = 1;

    private int $currentVersion = 0;

    /**
     * From BaseRepositoryInterface.
     *
     * @return array<Order>
     */
    public function findAll(): array
    {
        return array_map(
            fn(array $entry): Order => $entry['order'],
            $this->orders,
        );
    }

    /**
     * From OrderRepositoryInterface.
     */
    public function findById(int $id): ?Order
    {
        if (!isset($this->orders[$id])) {
            return null;
        }

        return $this->orders[$id]['order'];
    }

    /**
     * From OrderRepositoryInterface.
     */
    public function save(Order $order): Order
    {
        $this->currentVersion++;

        if ($order->id === 0) {
            $newOrder = new Order(
                id: $this->nextId++,
                customerEmail: $order->customerEmail,
                productId: $order->productId,
                quantity: $order->quantity,
                status: $order->status,
                createdAt: $order->createdAt,
            );
            $this->orders[$newOrder->id] = [
                'order' => $newOrder,
                'version' => $this->currentVersion,
            ];

            return $newOrder;
        }

        $this->orders[$order->id] = [
            'order' => $order,
            'version' => $this->currentVersion,
        ];

        return $order;
    }

    /**
     * From VersionedOrderRepositoryInterface.
     *
     * @return array<Order>
     */
    public function findByVersion(int $version): array
    {
        return array_map(
            fn(array $entry): Order => $entry['order'],
            array_filter(
                $this->orders,
                fn(array $entry): bool => $entry['version'] === $version,
            ),
        );
    }

    /**
     * From VersionedOrderRepositoryInterface.
     */
    public function getLatestVersion(): int
    {
        return $this->currentVersion;
    }
}
