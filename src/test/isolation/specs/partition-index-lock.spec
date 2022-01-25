# Partial Index test
#
# Make sure that an update which moves a row out of a partial index
# is handled correctly.  In early versions, an attempt at optimization
# broke this behavior, allowing anomalies.
#
# Any overlap between the transactions must cause a serialization failure.

setup
{
 CREATE TABLE test_t (id integer, val1 text, val2 integer) PARTITION BY RANGE(id);
 CREATE TABLE test_t_parted1 PARTITION OF test_t FOR VALUES FROM (1) TO (100) PARTITION BY RANGE(id);
 CREATE TABLE test_t_child1_parted1 PARTITION OF test_t_parted1 FOR VALUES FROM (1) TO (100);
 CREATE INDEX test_t_idx on test_t(id);
 CREATE INDEX test_parted1_idx on test_t_parted1(id);
}

teardown
{
 DROP TABLE test_t;
}

session s0
step s0analyze  { ANALYZE test_t; }

session s1
step s1begin	{ BEGIN; }
step s1select	{ SELECT * FROM test_t_child1_parted1; }
step s1pid      { SELECT pg_backend_pid(); }
step s1lock     { SELECT c.relname, l.pid, l.mode, l.granted FROM pg_locks l,
pg_class c WHERE l.relation = c.oid AND c.relname LIKE 'test_t%' ORDER BY c.relname, l.granted; }
step s1commit	{ COMMIT; }

session s2
step s2begin	{ BEGIN; }
step s2pid      { SELECT pg_backend_pid(); }
step s2drop	{ DROP INDEX test_t_idx; }
step s2commit	{ COMMIT; }

session s3
step s3begin    { BEGIN; }
step s3pid      { SELECT pg_backend_pid(); }
step s3drop     { DROP INDEX test_parted1_idx; }
step s3commit   { COMMIT; }

# Concurrency lock for partition tables
# will block drop statemt
permutation s1begin s2begin s1pid s2pid s0analyze s1select s2drop(s1commit) s1lock s1commit s2commit
permutation s1begin s3begin s1pid s3pid s0analyze s1select s3drop(s1commit) s1lock s1commit s3commit



# permutation s1b s2b s1s1 s2c1 s2d1 s1c1
# permutation s1b s2b s2d1 s1c1 s1s1 s2c1
#permutation s1b s2b s2d1 s1s1 s2c1 s1c1
#permutation s1b s2b s2d1 s1s1 s1c1 s2c1
