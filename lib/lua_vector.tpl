namespace  std
{
class vector
{
        TOLUA_TEMPLATE_BIND(T, __type__)

        void clear();
        int size() const;
        void resize(int new_size);
        void reserve(int new_capacity);

        const T& operator[] (int index)const;
        T& operator[] (int index);
        void push_back(const T& val);

        vector();
        ~vector();
};
}
