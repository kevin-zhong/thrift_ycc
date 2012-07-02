namespace std {
class pair
{
        TOLUA_TEMPLATE_BIND("F S", __pair__)
        
        pair();
        ~pair();
        F first;
        S second;
};

class map
{
	TOLUA_TEMPLATE_BIND("K V", __map__)
	
	bool empty();
	int size() const;
	
	void swap(map<K, V>& x);
	
	int erase(const K& x);
	void clear();

	map();
	~map();
};

class map_wrapper
{
	TOLUA_TEMPLATE_BIND("K V", __map__)
	typedef  map<K,V> TMap;
	
       static void set_kv(TMap& pmap, const K& key, const V& data);
       static pair<V,bool> get_kv(TMap& pmap, const K& key);
};

class map_iterator
{
	TOLUA_TEMPLATE_BIND("K V", __map__)
	typedef  map<K,V> TMap;

        map_iterator();
        ~map_iterator();

        void  init(TMap& pmap);
        bool  is_eof();
        void  advance();
        K key();
        V value();
};
}
