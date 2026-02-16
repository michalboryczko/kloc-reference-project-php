<?php

declare(strict_types=1);

namespace App\Service;

use App\Entity\Order;
use App\Repository\VersionedOrderRepositoryInterface;

/**
 * Service for versioned order operations.
 *
 * Contract test patterns:
 * - Constructor dependency on interface with 3-level hierarchy
 * - Method calls on interface methods from all hierarchy levels
 */
final readonly class VersionedOrderService
{
    public function __construct(
        private VersionedOrderRepositoryInterface $repository,
    ) {
    }

    public function getOrder(int $id): ?Order
    {
        return $this->repository->findById($id);
    }

    /**
     * @return array<Order>
     */
    public function getOrdersByVersion(int $version): array
    {
        return $this->repository->findByVersion($version);
    }

    /**
     * @return array<Order>
     */
    public function getAllOrders(): array
    {
        return $this->repository->findAll();
    }

    public function getCurrentVersion(): int
    {
        return $this->repository->getLatestVersion();
    }
}
