import { NextResponse } from 'next/server';

// Types for OCR response
interface InsuranceData {
    member_id: string;
    group_number: string;
    plan_name: string;
    plan_type: 'PPO' | 'HMO' | 'EPO' | 'POS';
    insurance_company: string;
    copay_primary_care: number;
    copay_specialist: number;
    copay_urgent_care: number;
    copay_emergency: number;
    deductible: number;
    deductible_met: number;
    out_of_pocket_max: number;
    out_of_pocket_current: number;
    effective_date: string;
    subscriber_name: string;
}

// Mock insurance data - will be replaced with real OCR logic
const MOCK_INSURANCE_DATA: InsuranceData = {
    member_id: "XYZ123456789",
    group_number: "GRP-98765",
    plan_name: "Blue Shield PPO Gold",
    plan_type: "PPO",
    insurance_company: "Blue Shield of California",
    copay_primary_care: 25,
    copay_specialist: 50,
    copay_urgent_care: 75,
    copay_emergency: 250,
    deductible: 1500,
    deductible_met: 850,
    out_of_pocket_max: 6000,
    out_of_pocket_current: 1200,
    effective_date: "2025-01-01",
    subscriber_name: "John Smith"
};

export async function POST(request: Request) {
    try {
        const formData = await request.formData();
        const file = formData.get('image') as File | null;

        if (!file) {
            return NextResponse.json(
                { error: 'No image file provided' },
                { status: 400 }
            );
        }

        console.log('Received OCR request for file:', file.name, 'Size:', file.size);

        // Simulate OCR processing delay
        await new Promise(resolve => setTimeout(resolve, 1500));

        // TODO: Replace with real OCR logic
        // const ocrService = new InsuranceOCRService();
        // const result = await ocrService.extractInsuranceData(file);
        // return NextResponse.json(result);

        return NextResponse.json({
            success: true,
            insurance_data: MOCK_INSURANCE_DATA,
            confidence: 0.95,
            processing_time_ms: 1500
        });
    } catch (error) {
        console.error('Error processing OCR:', error);
        return NextResponse.json(
            { error: 'Failed to process insurance card image' },
            { status: 500 }
        );
    }
}
