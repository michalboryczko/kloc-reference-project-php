<?php

declare(strict_types=1);

namespace App\Service;

use Symfony\Contracts\HttpClient\HttpClientInterface;

final readonly class PaypalGateway
{
    public function __construct(
        private HttpClientInterface $paypalClient,
    ) {
    }

    public function verify(int $orderId): bool
    {
        $response = $this->paypalClient->request('GET', '/orders/' . $orderId);

        return $response->getStatusCode() === 200;
    }
}
