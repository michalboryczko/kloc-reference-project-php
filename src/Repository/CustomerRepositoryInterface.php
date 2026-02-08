<?php

declare(strict_types=1);

namespace App\Repository;

use App\Entity\Address;
use App\Entity\Contact;
use App\Entity\Customer;

interface CustomerRepositoryInterface
{
    public function findById(int $id): ?Customer;

    public function save(Customer $customer): Customer;

    public function createCustomer(
        string $name,
        string $email,
        string $phone,
        string $street,
        string $city,
        string $postalCode,
        string $country,
    ): Customer;
}
