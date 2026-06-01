import { dbLib } from './db-lib';

describe('dbLib', () => {
    it('should work', () => {
        expect(dbLib()).toEqual('db-lib');
    })
})