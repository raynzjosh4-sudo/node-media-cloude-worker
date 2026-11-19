-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.users_table (
  id uuid NOT NULL,
  full_name text NOT NULL,
  email text,
  role USER-DEFINED DEFAULT 'customer'::app_role,
  profile_pic_url text,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  CONSTRAINT users_table_pkey PRIMARY KEY (id),
  CONSTRAINT users_table_id_fkey FOREIGN KEY (id) REFERENCES auth.users(id)
);
CREATE TABLE public.business_table (
  user_id uuid NOT NULL,
  legal_name text NOT NULL,
  phone_number text,
  physical_address text,
  city text,
  region text,
  latitude double precision,
  longitude double precision,
  updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  industry_group text,
  logo_url text,
  CONSTRAINT business_table_pkey PRIMARY KEY (user_id),
  CONSTRAINT business_table_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users_table(id)
);
CREATE TABLE public.pdfs_table (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL,
  title text NOT NULL,
  file_url text NOT NULL,
  file_size text,
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  CONSTRAINT pdfs_table_pkey PRIMARY KEY (id),
  CONSTRAINT pdfs_table_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users_table(id)
);
CREATE TABLE public.saved_items (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL,
  product_id uuid NOT NULL,
  quantity integer DEFAULT 1,
  selected_color text,
  selected_size text,
  product_snapshot jsonb DEFAULT '{}'::jsonb,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  CONSTRAINT saved_items_pkey PRIMARY KEY (id),
  CONSTRAINT saved_items_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users_table(id)
);
CREATE TABLE public.draft_orders (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL,
  entries_json jsonb NOT NULL DEFAULT '[]'::jsonb,
  status text DEFAULT 'DRAFT'::text,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  last_modified timestamp with time zone DEFAULT timezone('utc'::text, now()),
  CONSTRAINT draft_orders_pkey PRIMARY KEY (id),
  CONSTRAINT draft_orders_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users_table(id)
);
CREATE TABLE public.categories_table (
  id text NOT NULL,
  name text NOT NULL,
  image_url text,
  parent_id text,
  level integer DEFAULT 0,
  item_count integer DEFAULT 0,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  CONSTRAINT categories_table_pkey PRIMARY KEY (id),
  CONSTRAINT categories_table_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.categories_table(id)
);
CREATE TABLE public.promotions_table (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  title text NOT NULL,
  subtitle text,
  action_text text,
  image_urls jsonb NOT NULL DEFAULT '[]'::jsonb,
  priority integer DEFAULT 0,
  is_active boolean DEFAULT true,
  starts_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  expires_at timestamp with time zone,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  CONSTRAINT promotions_table_pkey PRIMARY KEY (id)
);
CREATE TABLE public.products_table (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  sku text NOT NULL UNIQUE,
  name text NOT NULL,
  brand text,
  slug text NOT NULL UNIQUE,
  srp numeric NOT NULL DEFAULT 0,
  price_tiers jsonb NOT NULL DEFAULT '[]'::jsonb,
  supplier_id uuid NOT NULL,
  category_id text NOT NULL,
  hs_code text,
  weight_kg numeric,
  volume_cbm numeric,
  origin_country text,
  unbs_number text,
  denier text,
  material text,
  current_stock integer DEFAULT 0,
  lead_time_days integer DEFAULT 0,
  warehouse_loc text,
  image_url text NOT NULL,
  media_urls jsonb DEFAULT '[]'::jsonb,
  aspect_ratio numeric DEFAULT 1.0,
  seo_title text,
  seo_description text,
  search_keywords ARRAY,
  available_colors jsonb DEFAULT '[]'::jsonb,
  available_sizes jsonb DEFAULT '[]'::jsonb,
  available_materials jsonb DEFAULT '[]'::jsonb,
  variant_label text DEFAULT 'Size'::text,
  support_info jsonb DEFAULT '{}'::jsonb,
  trading_terms jsonb DEFAULT '{}'::jsonb,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  CONSTRAINT products_table_pkey PRIMARY KEY (id),
  CONSTRAINT products_table_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.users_table(id),
  CONSTRAINT products_table_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories_table(id)
);
CREATE TABLE public.orders_table (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL,
  total_amount numeric NOT NULL DEFAULT 0,
  pdf_id uuid,
  status text NOT NULL DEFAULT 'pending'::text CHECK (status = ANY (ARRAY['pending'::text, 'processing'::text, 'shipped'::text, 'delivered'::text, 'cancelled'::text])),
  entries_json jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  CONSTRAINT orders_table_pkey PRIMARY KEY (id),
  CONSTRAINT orders_table_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users_table(id),
  CONSTRAINT orders_table_pdf_id_fkey FOREIGN KEY (pdf_id) REFERENCES public.pdfs_table(id)
);
CREATE TABLE public.user_tokens (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL,
  device_token text NOT NULL,
  device_type text,
  last_active_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  updated_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  CONSTRAINT user_tokens_pkey PRIMARY KEY (id),
  CONSTRAINT user_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users_table(id)
);
CREATE TABLE public.notifications_table (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL,
  title text NOT NULL,
  description text,
  category text NOT NULL CHECK (category = ANY (ARRAY['all'::text, 'orders'::text, 'inventory'::text, 'logistics'::text, 'security'::text, 'finance'::text, 'system'::text])),
  is_unread boolean DEFAULT true,
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  CONSTRAINT notifications_table_pkey PRIMARY KEY (id),
  CONSTRAINT notifications_table_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users_table(id)
);
CREATE TABLE public.search_history (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL,
  query text NOT NULL,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
  CONSTRAINT search_history_pkey PRIMARY KEY (id),
  CONSTRAINT search_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users_table(id)
);
CREATE TABLE public.legal_terms (
  id text NOT NULL,
  title text NOT NULL,
  content text NOT NULL,
  updated_at timestamp with time zone DEFAULT now(),
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT legal_terms_pkey PRIMARY KEY (id)
);
CREATE TABLE public.supplier_orders (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  order_id text NOT NULL UNIQUE,
  user_id uuid NOT NULL,
  supplier_id text NOT NULL,
  business_name text NOT NULL,
  business_phone text NOT NULL,
  business_city text NOT NULL,
  business_address text NOT NULL,
  latitude double precision,
  longitude double precision,
  total_amount numeric NOT NULL,
  entries_json jsonb NOT NULL DEFAULT '[]'::jsonb,
  pdf_id uuid,
  status text NOT NULL DEFAULT 'new'::text CHECK (status = ANY (ARRAY['new'::text, 'seen'::text, 'processing'::text, 'completed'::text, 'cancelled'::text])),
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  pdf_url text,
  CONSTRAINT supplier_orders_pkey PRIMARY KEY (id),
  CONSTRAINT supplier_orders_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users_table(id),
  CONSTRAINT supplier_orders_pdf_id_fkey FOREIGN KEY (pdf_id) REFERENCES public.pdfs_table(id)
);
CREATE TABLE public.records (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  contact_name text NOT NULL,
  item_name text NOT NULL,
  reference_tag text,
  unit text NOT NULL DEFAULT 'Units'::text,
  target_value numeric NOT NULL DEFAULT 0,
  current_value numeric NOT NULL DEFAULT 0,
  type text NOT NULL CHECK (type = ANY (ARRAY['credit'::text, 'debt'::text, 'standard'::text])),
  contact_image_url text,
  grand_total numeric NOT NULL DEFAULT 0,
  is_archived boolean NOT NULL DEFAULT false,
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  breakdown_items_json text NOT NULL DEFAULT '[]'::text,
  timeline_json text NOT NULL DEFAULT '[]'::text,
  reminder_date timestamp with time zone,
  reminder_time text,
  reminder_is_recurring boolean NOT NULL DEFAULT false,
  CONSTRAINT records_pkey PRIMARY KEY (id),
  CONSTRAINT records_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);
CREATE TABLE public.record_breakdown_items (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  record_id uuid NOT NULL,
  name text NOT NULL,
  quantity integer NOT NULL DEFAULT 1,
  amount numeric NOT NULL DEFAULT 0,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT record_breakdown_items_pkey PRIMARY KEY (id),
  CONSTRAINT record_breakdown_items_record_id_fkey FOREIGN KEY (record_id) REFERENCES public.records(id)
);
CREATE TABLE public.record_timeline (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  record_id uuid NOT NULL,
  message text NOT NULL DEFAULT 'New entry'::text,
  total numeric NOT NULL DEFAULT 0,
  balance_after numeric NOT NULL DEFAULT 0,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT record_timeline_pkey PRIMARY KEY (id),
  CONSTRAINT record_timeline_record_id_fkey FOREIGN KEY (record_id) REFERENCES public.records(id)
);
CREATE TABLE public.record_reminders (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  record_id uuid NOT NULL UNIQUE,
  reminder_date date,
  reminder_time text,
  is_recurring boolean NOT NULL DEFAULT false,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT record_reminders_pkey PRIMARY KEY (id),
  CONSTRAINT record_reminders_record_id_fkey FOREIGN KEY (record_id) REFERENCES public.records(id)
);

-- =========================================================================
-- Email Assets & Storage Setup for Professional Templates
-- =========================================================================

-- 1. Create Public Storage Bucket 'email-assets'
INSERT INTO storage.buckets (id, name, public)
VALUES ('email-assets', 'email-assets', true)
ON CONFLICT (id) DO UPDATE SET public = true;

-- 2. Allow public access to view images
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Public Access to email-assets'
  ) THEN
    CREATE POLICY "Public Access to email-assets"
    ON storage.objects FOR SELECT
    USING ( bucket_id = 'email-assets' );
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'Allow uploads to email-assets'
  ) THEN
    CREATE POLICY "Allow uploads to email-assets"
    ON storage.objects FOR INSERT
    WITH CHECK ( bucket_id = 'email-assets' );
  END IF;
END $$;

-- 3. Table for storing and querying Email Template Images & URLs
CREATE TABLE IF NOT EXISTS public.email_images (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  key text UNIQUE NOT NULL,
  filename text NOT NULL,
  image_url text NOT NULL,
  description text,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now())
);

-- 4. Pre-populate Email Images URLs
INSERT INTO public.email_images (key, filename, image_url, description)
VALUES 
  ('confirm_email', 'confirmemail.jpg', 'https://lihoygvdnnfqodjjxqnz.supabase.co/storage/v1/object/public/email-assets/confirmemail.jpg', 'Email verification OTP header banner'),
  ('reset_password', 'resetpassword.jpg', 'https://lihoygvdnnfqodjjxqnz.supabase.co/storage/v1/object/public/email-assets/resetpassword.jpg', 'Password reset header banner'),
  ('verify_login', 'verifylogin.jpg', 'https://lihoygvdnnfqodjjxqnz.supabase.co/storage/v1/object/public/email-assets/verifylogin.jpg', 'Login verification / 2FA header banner'),
  ('welcome', 'welcomeimage.jpg', 'https://lihoygvdnnfqodjjxqnz.supabase.co/storage/v1/object/public/email-assets/welcomeimage.jpg', 'Welcome to N.O.D.E. header banner'),
  ('security_alert', 'securitysigninalart.jpg', 'https://lihoygvdnnfqodjjxqnz.supabase.co/storage/v1/object/public/email-assets/securitysigninalart.jpg', 'Security sign-in alert header banner'),
  ('order_confirmation', 'orderconfirmation.jpg', 'https://lihoygvdnnfqodjjxqnz.supabase.co/storage/v1/object/public/email-assets/orderconfirmation.jpg', 'Order confirmation header banner'),
  ('order_confirmed', 'orderconfirmedimage.jpg', 'https://lihoygvdnnfqodjjxqnz.supabase.co/storage/v1/object/public/email-assets/orderconfirmedimage.jpg', 'Order confirmed header banner'),
  ('order_status', 'orderstatusupdate.jpg', 'https://lihoygvdnnfqodjjxqnz.supabase.co/storage/v1/object/public/email-assets/orderstatusupdate.jpg', 'Order status update header banner')
ON CONFLICT (key) DO UPDATE SET 
  image_url = EXCLUDED.image_url,
  description = EXCLUDED.description;
