-- Document Verification Platform Database Schema
-- Run this in Supabase SQL Editor

-- Enable UUID extension (usually already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Officer profiles table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS officer_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name TEXT NOT NULL,
  department TEXT,
  role TEXT DEFAULT 'OFFICER' CHECK (role IN ('OFFICER', 'ADMIN')),
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Verification requests table
CREATE TABLE IF NOT EXISTS verification_requests (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  created_at TIMESTAMPTZ DEFAULT now(),
  status TEXT DEFAULT 'PROCESSING' CHECK (status IN ('PROCESSING', 'COMPLETED', 'FAILED')),
  document_type TEXT,
  raw_response JSONB,
  fraud_flag BOOLEAN DEFAULT false
);

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  request_id UUID REFERENCES verification_requests(id) ON DELETE CASCADE,
  officer_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  officer_decision TEXT CHECK (officer_decision IN ('APPROVE', 'REJECT', 'REVIEW')),
  was_overridden BOOLEAN DEFAULT false,
  override_reason TEXT,
  latency_ms INTEGER,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_verification_requests_status ON verification_requests(status);
CREATE INDEX IF NOT EXISTS idx_verification_requests_created_at ON verification_requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_request_id ON audit_logs(request_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_officer_id ON audit_logs(officer_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- Function to auto-create officer profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.officer_profiles (id, full_name, department, role)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'full_name', 'New Officer'),
    COALESCE(NEW.raw_user_meta_data->>'department', ''),
    COALESCE(NEW.raw_user_meta_data->>'role', 'OFFICER')
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create profile on signup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Row Level Security
ALTER TABLE officer_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE verification_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Policies: Officers can read their own profile
CREATE POLICY "Users can view own profile" ON officer_profiles
  FOR SELECT USING (auth.uid() = id);

-- Policies: Admins can view all profiles
-- Helper function to safely check for admin role (bypasses RLS to avoid recursion)
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1
    FROM officer_profiles
    WHERE id = auth.uid() AND role = 'ADMIN'
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Policies: Admins can view all profiles
CREATE POLICY "Admins can view all profiles" ON officer_profiles
  FOR SELECT USING (
    public.is_admin()
  );

-- Policies: All authenticated users can create verification requests
CREATE POLICY "Authenticated users can create requests" ON verification_requests
  FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

CREATE POLICY "Authenticated users can view requests" ON verification_requests
  FOR SELECT USING (auth.uid() IS NOT NULL);

CREATE POLICY "Authenticated users can update requests" ON verification_requests
  FOR UPDATE USING (auth.uid() IS NOT NULL);

-- Policies: All authenticated users can create and view audit logs
CREATE POLICY "Authenticated users can create audit logs" ON audit_logs
  FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

CREATE POLICY "Authenticated users can view audit logs" ON audit_logs
  FOR SELECT USING (auth.uid() IS NOT NULL);
