<?php

declare(strict_types=1);

namespace App\Ui\Rest\Controller;

use App\Service\PaypalGateway;
use App\Ui\Messenger\Message\AuditLogMessage;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Messenger\MessageBusInterface;
use Symfony\Component\Routing\Attribute\Route;

#[Route('/api/payments')]
final class PaymentController extends AbstractController
{
    public function __construct(
        private readonly PaypalGateway $paypalGateway,
        private readonly MessageBusInterface $messageBus,
    ) {
    }

    #[Route('/{id}/verify', name: 'payment_verify', methods: ['POST'])]
    public function verify(int $id): JsonResponse
    {
        $verified = $this->paypalGateway->verify($id);

        $this->messageBus->dispatch(new AuditLogMessage($id, 'verified'));

        return $this->json(
            ['verified' => $verified],
            $verified ? Response::HTTP_OK : Response::HTTP_PAYMENT_REQUIRED,
        );
    }
}
