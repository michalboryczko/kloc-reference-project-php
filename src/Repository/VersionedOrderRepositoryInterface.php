<?php

declare(strict_types=1);

namespace App\Repository;

use App\Entity\Order;

/**
 * Interface chain: VersionedOrderRepositoryInterface
 *   extends OrderRepositoryInterface
 *     extends BaseRepositoryInterface
 *
 * 3-level interface hierarchy for contract testing.
 */
interface VersionedOrderRepositoryInterface extends OrderRepositoryInterface
{
    /**
     * @return array<Order>
     */
    public function findByVersion(int $version): array;

    public function getLatestVersion(): int;
}
