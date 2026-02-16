<?php

declare(strict_types=1);

namespace App\Service;

use App\Component\AuditableInterface;
use App\Entity\Order;
use App\Repository\OrderRepositoryInterface;

/**
 * Service for audit operations.
 *
 * Contract test patterns:
 * - Constructor with interface dependencies
 * - Method calls on injected interfaces
 * - Provides USED BY edges for AuditableInterface and OrderRepositoryInterface
 */
final readonly class AuditService
{
    public function __construct(
        private AuditableInterface $auditable,
        private OrderRepositoryInterface $orderRepository,
    ) {
    }

    /**
     * @return array<string>
     */
    public function getRecentAuditLog(): array
    {
        return $this->auditable->getAuditLog();
    }

    public function getAuditedOrder(int $id): ?Order
    {
        $order = $this->orderRepository->findById($id);

        return $order;
    }

    /**
     * @return array<Order>
     */
    public function getAllOrders(): array
    {
        return $this->orderRepository->findAll();
    }
}
