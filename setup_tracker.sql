-- Run this once in Supabase → SQL Editor
-- Creates a persistent table to track outreach emails sent,
-- so the dedup list survives Railway redeploys.

CREATE TABLE IF NOT EXISTS outreach_contacted (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email text UNIQUE NOT NULL,
    company text,
    batch text,
    contacted_at timestamptz DEFAULT now()
);

-- Optional: backfill the 18 founders already contacted today
-- (so they don't get duplicate emails if re-run)
INSERT INTO outreach_contacted (email, company, batch) VALUES
    ('charles@pleo.com', 'Pleo', 'batch1'),
    ('alastair.mcgill@moneyhub.com', 'Moneyhub', 'batch1'),
    ('gsaini@cleo.com', 'Cleo', 'batch1'),
    ('tom.adams@tessian.com', 'Tessian', 'batch1'),
    ('harriet@butternutbox.com', 'Butternut Box', 'batch1'),
    ('pierre-hugues.jeanneret@onfido.com', 'Onfido', 'batch1'),
    ('alexander@marshmallow.com', 'Marshmallow', 'batch1'),
    ('founders@paddle.com', 'Paddle', 'batch1'),
    ('barbara.sullivan@vendr.com', 'Vendr', 'batch2'),
    ('anahita@mintlify.com', 'Mintlify', 'batch2'),
    ('martin.tapia@phantombuster.com', 'Phantombuster', 'batch2'),
    ('uripri_2007@senja.com', 'Senja', 'batch2'),
    ('maria.corpuz@fathom.com', 'Fathom', 'batch2'),
    ('benedikt@userlist.com', 'Userlist', 'batch2'),
    ('maud@crisp.com', 'Crisp', 'batch2'),
    ('ncooke@vendasta.com', 'Vendasta', 'batch2')
ON CONFLICT (email) DO NOTHING;
