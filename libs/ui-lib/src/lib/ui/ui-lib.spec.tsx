import { render } from '@testing-library/react';

import DataPlatformsUiLib from './ui-lib';

describe('DataPlatformsUiLib', () => {

  it('should render successfully', () => {
    const { baseElement } = render(<DataPlatformsUiLib />);
    expect(baseElement).toBeTruthy();
  });

});
