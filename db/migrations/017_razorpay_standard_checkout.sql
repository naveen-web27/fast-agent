ALTER TABLE payments ADD COLUMN IF NOT EXISTS razorpay_order_id TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS payments_razorpay_order_id_idx ON payments (razorpay_order_id);