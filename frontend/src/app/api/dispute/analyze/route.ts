import { NextRequest, NextResponse } from 'next/server';

// Dispute backend URL
const DISPUTE_BACKEND_URL = process.env.DISPUTE_BACKEND_URL || 'http://localhost:8001';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const files = formData.getAll('files') as File[];
    const insurancePlan = formData.get('insurance_plan') as string;
    const insuranceName = formData.get('insurance_name') as string;

    if (!files || files.length === 0) {
      return NextResponse.json(
        { success: false, error: 'No files uploaded' },
        { status: 400 }
      );
    }

    console.log(`Received ${files.length} files`);
    console.log(`Insurance: ${insuranceName} (${insurancePlan})`);

    // Forward files and insurance info to Python backend
    const backendFormData = new FormData();
    for (const file of files) {
      backendFormData.append('files', file);
    }
    if (insurancePlan) {
      backendFormData.append('insurance_plan', insurancePlan);
    }
    if (insuranceName) {
      backendFormData.append('insurance_name', insuranceName);
    }

    try {
      const response = await fetch(`${DISPUTE_BACKEND_URL}/api/dispute/analyze`, {
        method: 'POST',
        body: backendFormData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Backend error:', errorText);
        throw new Error(`Backend returned ${response.status}`);
      }

      const result = await response.json();
      console.log('Backend response received');
      return NextResponse.json(result);

    } catch (backendError) {
      console.error('Backend connection failed:', backendError);
      return NextResponse.json({
        success: false,
        error: 'Backend service not available. Please start the dispute API server: cd dispute && python api_server.py'
      }, { status: 503 });
    }

  } catch (error) {
    console.error('Error processing request:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to process request' },
      { status: 500 }
    );
  }
}
