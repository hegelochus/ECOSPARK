-- Run once in Supabase: SQL Editor -> New query -> paste -> Run
create extension if not exists pgcrypto;

create table if not exists profiles (
  email text primary key,
  name text,
  terms_version text,
  terms_accepted_at timestamptz,
  created_at timestamptz default now()
);

create table if not exists posts (
  id uuid primary key default gen_random_uuid(),
  author_email text not null,
  author_name text,
  title text not null,
  body text not null,
  image_paths text[] default '{}',
  created_at timestamptz default now()
);

create table if not exists comments (
  id uuid primary key default gen_random_uuid(),
  post_id uuid not null references posts(id) on delete cascade,
  author_email text not null,
  author_name text,
  body text not null,
  created_at timestamptz default now()
);

create table if not exists news (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  body text not null,
  link text,
  author_email text,
  created_at timestamptz default now()
);

-- Lock the tables: only the app's server-side service key can read/write them.
alter table profiles enable row level security;
alter table posts    enable row level security;
alter table comments enable row level security;
alter table news     enable row level security;

-- Public bucket for post photos (anyone can view a photo; only the app can upload/delete).
insert into storage.buckets (id, name, public)
values ('post-images', 'post-images', true)
on conflict (id) do nothing;
